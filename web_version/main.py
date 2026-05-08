import os
import sys
import time
import uuid
import shutil
import subprocess
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = FastAPI(title="遥感样本制作工具")

# 硬编码的 Python 路径（ArcGIS 环境）
PYTHON_EXE = r"C:\Python27\ArcGIS10.8\python.exe"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
BASE_OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
TASKS_FILE = os.path.join(BASE_DIR, "tasks.json")

# 存储运行中的进程，用于停止任务
running_processes = {}

def make_dirs_safe(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            print(f"Created directory: {path}")
        except Exception as e:
            print(f"Warning: Could not create directory {path}: {e}")
            print("Please create the directory manually:")
            print(f"  mkdir {path}")

make_dirs_safe(BASE_UPLOAD_DIR)
make_dirs_safe(BASE_OUTPUT_DIR)

if not os.path.exists(TASKS_FILE):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        f.write("{}")
    print(f"[init] Created empty tasks.json at {TASKS_FILE}")
else:
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            with open(TASKS_FILE, "w", encoding="utf-8") as f:
                f.write("{}")
            print(f"[init] tasks.json was empty, reset to {{}}")
        else:
            json.loads(content)
            print(f"[init] tasks.json OK, contains {len(content)} bytes")
    except (ValueError, IOError) as e:
        print(f"[init] tasks.json invalid ({e}), resetting to {{}}")
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            f.write("{}")

def safe_open(filepath, mode='r', encoding='utf-8'):
    if sys.version_info[0] < 3:
        import codecs
        return codecs.open(filepath, mode, encoding)
    else:
        return open(filepath, mode, encoding=encoding)

def load_tasks():
    try:
        with safe_open(TASKS_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, IOError, ValueError) as e:
        print(f"[load_tasks] parse error: {e}")
        try:
            backup = TASKS_FILE + ".corrupt." + str(int(time.time()))
            shutil.copy2(TASKS_FILE, backup)
            print(f"[load_tasks] backed up to {backup}")
        except Exception:
            pass
        return {}

def save_tasks(tasks):
    temp_file = TASKS_FILE + ".tmp"
    try:
        with safe_open(temp_file, "w") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"[save_tasks] temp write FAIL: {e}")
        return
    try:
        if os.path.exists(TASKS_FILE):
            os.remove(TASKS_FILE)
        os.rename(temp_file, TASKS_FILE)
        print(f"[save_tasks] OK, {len(tasks)} task(s)")
    except Exception as e:
        print(f"[save_tasks] rename FAIL: {e}, fallback direct write")
        try:
            with safe_open(TASKS_FILE, "w") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
        except Exception as e2:
            print(f"[save_tasks] direct write FAIL: {e2}")

def get_log_file(task_id):
    tasks = load_tasks()
    task = tasks.get(task_id, {})
    output_path = task.get("output_path", "")
    if output_path:
        return os.path.join(output_path, task_id, "task.log")
    return os.path.join(BASE_OUTPUT_DIR, task_id, "task.log")

def read_task_logs(task_id):
    log_file = get_log_file(task_id)
    lines = []
    if os.path.exists(log_file):
        try:
            with safe_open(log_file, "r") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
        except:
            return []
    fallback = os.path.join(BASE_OUTPUT_DIR, task_id, "task.log")
    if not lines and fallback != log_file and os.path.exists(fallback):
        try:
            with safe_open(fallback, "r") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
        except:
            return []
    seen = set()
    result = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            result.append(line)
    return result

class ProcessRequest(BaseModel):
    task_id: str
    patch_size: str = "128x128"
    overlap_ratio: str = "25%"
    author_abbr: str = ""
    output_path: str = ""
    output_formats: dict = {
        "tif": True,
        "jpg_true": True,
        "jpg_false": True
    }
    bands_true: str = "3,2,1"
    bands_false: str = "4,3,2"

@app.get("/")
async def root():
    return {"message": "遥感样本制作工具 API", "version": "1.0"}

@app.get("/api/detect-python")
async def detect_python():
    # 此接口已禁用，Python 路径硬编码为 C:\Python27\ArcGIS10.4\python.exe
    return {"found": True, "path": PYTHON_EXE, "version": "Python 2.7 (ArcGIS 10.4)"}

@app.post("/api/upload")
async def upload_files(
    task_id: str = Form(...),
    image_file: UploadFile = File(...),
    label_files: List[UploadFile] = File(...)
):
    task_dir = os.path.join(BASE_UPLOAD_DIR, task_id)

    try:
        os.makedirs(task_dir, exist_ok=True)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"无法创建上传目录 {task_dir}: {e}。请确保目录 {BASE_UPLOAD_DIR} 存在且有写入权限。")

    image_path = os.path.join(task_dir, image_file.filename)
    label_path = ""
    uploaded_label_files = []

    try:
        with open(image_path, "wb") as f:
            shutil.copyfileobj(image_file.file, f)
        for lf in label_files:
            lf_path = os.path.join(task_dir, lf.filename)
            with open(lf_path, "wb") as f:
                shutil.copyfileobj(lf.file, f)
            uploaded_label_files.append(lf.filename)
            if lf.filename.lower().endswith(".shp"):
                label_path = lf_path
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"文件写入失败: {e}")

    if not label_path:
        for lf in label_files:
            candidate = os.path.join(task_dir, lf.filename)
            if candidate.lower().endswith((".tif", ".tiff")):
                label_path = candidate
                break
        if not label_path and uploaded_label_files:
            label_path = os.path.join(task_dir, uploaded_label_files[0])

    tasks = load_tasks()
    tasks[task_id] = {
        "status": "uploaded",
        "progress": 0,
        "message": "文件上传完成",
        "image_path": image_path,
        "label_path": label_path,
        "uploaded_label_files": uploaded_label_files,
        "log_message": ""
    }
    save_tasks(tasks)

    return {"task_id": task_id, "status": "uploaded", "message": "文件上传成功", "label_files": uploaded_label_files}

@app.post("/api/process")
async def process_request(req: ProcessRequest):
    tasks = load_tasks()
    if req.task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[req.task_id]
    task["status"] = "processing"
    task["patch_size"] = req.patch_size
    task["overlap_ratio"] = req.overlap_ratio
    task["author_abbr"] = req.author_abbr
    task["output_path"] = req.output_path
    task["output_formats"] = req.output_formats
    task["bands_true"] = req.bands_true
    task["bands_false"] = req.bands_false
    task["message"] = "正在启动处理..."
    save_tasks(tasks)

    if req.output_path:
        output_dir = os.path.join(req.output_path, req.task_id)
    else:
        output_dir = os.path.join(BASE_OUTPUT_DIR, req.task_id)
    make_dirs_safe(output_dir)

    log_file = os.path.join(output_dir, "task.log")
    with safe_open(log_file, "w") as f:
        f.write("[启动] 开始处理任务\n")

    params_json = json.dumps({
        "task_id": req.task_id,
        "patch_size": req.patch_size,
        "overlap_ratio": req.overlap_ratio,
        "author_abbr": req.author_abbr,
        "output_formats": req.output_formats,
        "bands_true": req.bands_true,
        "bands_false": req.bands_false,
        "log_file": log_file,
        "tasks_file": TASKS_FILE
    }, ensure_ascii=False)

    python_exe = PYTHON_EXE

    cmd = [
        python_exe,
        os.path.join(SCRIPT_DIR, "processor.py"),
        req.task_id,
        task["image_path"],
        task["label_path"],
        output_dir,
        params_json
    ]

    try:
        if os.name == 'nt':
            proc = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            proc = subprocess.Popen(cmd, start_new_session=True)

        # 保存进程引用，用于停止任务
        running_processes[req.task_id] = proc

        def check_process():
            try:
                returncode = proc.wait(timeout=86400)
                # 进程结束后从字典中移除
                if req.task_id in running_processes:
                    del running_processes[req.task_id]
                if returncode != 0:
                    tasks_inner = load_tasks()
                    if req.task_id in tasks_inner and tasks_inner[req.task_id]["status"] == "processing":
                        tasks_inner[req.task_id]["status"] = "error"
                        tasks_inner[req.task_id]["message"] = "处理进程异常退出，错误码: {0}".format(returncode)
                        save_tasks(tasks_inner)
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass

        import threading
        t = threading.Thread(target=check_process, daemon=True)
        t.start()

    except Exception as e:
        task["status"] = "error"
        task["message"] = "启动处理失败: " + str(e)
        save_tasks(tasks)

    return {"task_id": req.task_id, "status": "processing", "message": "处理已启动"}

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    tasks = load_tasks()
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_id]

    logs = read_task_logs(task_id)
    log_message = logs[-1] if logs else ""

    download_url = None
    if task["status"] == "completed":
        download_url = f"/api/download/{task_id}"

    return {
        "task_id": task_id,
        "status": task["status"],
        "progress": task.get("progress", 0),
        "message": task.get("message", ""),
        "log_message": log_message,
        "download_url": download_url
    }

@app.get("/api/logs/{task_id}")
async def get_logs(task_id: str):
    tasks = load_tasks()
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    logs = read_task_logs(task_id)
    return {"logs": logs}

@app.get("/api/download/{task_id}")
async def download_result(task_id: str):
    tasks = load_tasks()
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_id]
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Task not completed yet")

    output_dir = os.path.join(BASE_OUTPUT_DIR, task_id)
    zip_path = os.path.join(BASE_OUTPUT_DIR, f"{task_id}.zip")

    if not os.path.exists(zip_path):
        if os.path.exists(output_dir):
            shutil.make_archive(zip_path.replace(".zip", ""), "zip", output_dir)

    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="Output not found")

    return FileResponse(zip_path, filename=f"遥感样本_{task_id}.zip", media_type="application/zip")

@app.post("/api/stop/{task_id}")
async def stop_task(task_id: str):
    tasks = load_tasks()
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_id]
    if task["status"] != "processing":
        raise HTTPException(status_code=400, detail="Task is not processing")

    # 停止进程
    if task_id in running_processes:
        proc = running_processes[task_id]
        try:
            if os.name == 'nt':
                # Windows 上使用 taskkill 终止进程组
                import signal
                proc.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                # Unix 系统使用 SIGTERM
                proc.terminate()
            # 等待进程结束
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            print(f"[stop_task] Process terminated for task {task_id}")
        except Exception as e:
            print(f"[stop_task] Error terminating process: {e}")
        finally:
            if task_id in running_processes:
                del running_processes[task_id]

    # 删除本次任务产生的文件（保留其他任务的文件）
    try:
        # 删除上传目录中的任务文件
        upload_dir = os.path.join(BASE_UPLOAD_DIR, task_id)
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)
            print(f"[stop_task] Deleted upload dir: {upload_dir}")

        # 删除输出目录中的任务文件
        output_path = task.get("output_path", "")
        if output_path:
            output_dir = os.path.join(output_path, task_id)
        else:
            output_dir = os.path.join(BASE_OUTPUT_DIR, task_id)
        
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            print(f"[stop_task] Deleted output dir: {output_dir}")

        # 删除可能存在的 zip 文件
        zip_path = os.path.join(BASE_OUTPUT_DIR, f"{task_id}.zip")
        if os.path.exists(zip_path):
            os.remove(zip_path)
            print(f"[stop_task] Deleted zip file: {zip_path}")
    except Exception as e:
        print(f"[stop_task] Error cleaning up files: {e}")

    # 更新任务状态
    task["status"] = "stopped"
    task["message"] = "任务已停止"
    save_tasks(tasks)

    return {"task_id": task_id, "status": "stopped", "message": "任务已停止并清理完成"}

@app.get("/api/tasks")
async def list_tasks():
    tasks = load_tasks()
    return [{"task_id": k, "status": v["status"], "message": v.get("message", "")} for k, v in tasks.items()]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
