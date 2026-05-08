# -*- coding: utf-8 -*-
import os
import sys
import re
import glob
import shutil
import time
import traceback
import gc
import json
import io
import datetime
import subprocess

# Python 2 / 3 兼容
try:
    unicode
except NameError:
    unicode = str


DLMC_RENAME_MAP = {
    u"水田": u"水田",
    u"水浇地": u"水浇地",
    u"旱地": u"旱地",
    u"果园": u"园地",
    u"茶园": u"园地",
    u"其他园地": u"园地",
    u"乔木林地": u"林地",
    u"竹林地": u"林地",
    u"灌木林地": u"林地",
    u"其他林地": u"林地",
    u"其他草地": u"其他草地",
    u"河流水面": u"河流水面",
    u"湖泊水面": u"不考虑",
    u"水库水面": u"不考虑",
    u"坑塘水面": u"坑塘水面",
    u"养殖坑塘": u"养殖池塘",
    u"沟渠": u"沟渠",
    u"水工建筑用地": u"水工建筑用地",
    u"内陆滩涂": u"内陆滩涂",
    u"沿海滩涂": u"沿海滩涂",
    u"盐田": u"盐田",
    u"盐碱地": u"不考虑",
    u"沼泽地": u"不考虑",
    u"城镇住宅用地": u"农村、城市建筑用地",
    u"农村宅基地": u"农村、城市建筑用地",
    u"工业用地": u"工矿仓储用地",
    u"物流仓储用地": u"工矿仓储用地",
    u"商业服务业设施用地": u"不考虑",
    u"机关团体新闻出版用地": u"不考虑",
    u"科教文卫用地": u"不考虑",
    u"公用设施用地": u"不考虑",
    u"特殊用地": u"不考虑",
    u"采矿用地": u"工矿仓储用地",
    u"广场用地": u"不考虑",
    u"公园与绿地": u"公园与绿地",
    u"设施农用地": u"设施农用地",
    u"农村道路": u"农村道路",
    u"公路用地": u"公路用地",
    u"城镇村道路用地": u"城镇村道路用地",
    u"交通服务场站用地": u"不考虑",
    u"港口码头用地": u"港口码头用地",
    u"管道运输用地": u"不考虑",
    u"铁路用地": u"铁路用地",
    u"裸岩石砾地": u"裸地",
    u"可调整养殖坑塘": u"养殖池塘",
    u"可调整果园": u"园地",
    u"可调整其他园地": u"园地",
    u"可调整乔木林地": u"林地",
    u"可调整茶园": u"园地",
    u"马尾藻": u"马尾藻",
    u"浒苔": u"浒苔",
}
DLMC_IGNORE_NAME = u"不考虑"

# --- 1. 先导入界面库 ---
try:
    import Tkinter as tk
    import ttk
    import tkFileDialog as filedialog
    import ScrolledText as scrolledtext
    import tkMessageBox as messagebox
except ImportError:
    import tkinter as tk
    from tkinter import ttk, filedialog, scrolledtext, messagebox

# --- 2. 导入核心计算库 ---
try:
    from scipy.ndimage import binary_dilation
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import imageio
    HAS_IMAGEIO = True
except ImportError:
    HAS_IMAGEIO = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from scipy import misc as scipy_misc
    HAS_SCIPY_IMSAVE = hasattr(scipy_misc, "imsave")
except ImportError:
    HAS_SCIPY_IMSAVE = False

HAS_GDAL = False

# --- 3. 最后导入 ArcPy ---
try:
    import arcpy
    import numpy as np
    from arcpy.sa import *

    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput = True
    arcpy.env.compression = "NONE"
    arcpy.env.pyramid = "NONE"  # 禁止生成金字塔，节约计算
    HAS_ARCPY = True
except Exception as e:
    HAS_ARCPY = False
    print("Warning: ArcPy initialization failed - " + str(e))


class GeoCutterDynamicField:
    def __init__(self, root):
        self.root = root
        self.root.title(u"遥感样本制作工具")
        self.root.geometry("950x850")

        self.patch_options = ["128x128", "256x256", "512x512"]
        self.overlap_options = [u"50%", u"25%"]
        self.patch_size_var = tk.StringVar(value="128x128")
        self.overlap_ratio_var = tk.StringVar(value=u"25%")
        self.stride_var = tk.StringVar(value="384x384")

        self.input_path = tk.StringVar()
        self.mask_input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.author_abbr_var = tk.StringVar(value="")

        self.smart_select_var = tk.BooleanVar(value=True)
        self.buffer_size_var = tk.IntVar(value=1)

        self.out_tif_var = tk.BooleanVar(value=True)
        self.out_jpg_true_var = tk.BooleanVar(value=True)
        self.out_jpg_false_var = tk.BooleanVar(value=True)
        self.export_geojson_var = tk.BooleanVar(value=True)

        self.bands_true_var = tk.StringVar(value="3,2,1")
        self.bands_false_var = tk.StringVar(value="4,3,2")

        self.current_img = ""
        self.current_mask = ""
        self.current_vector = ""
        self.patch_index_path = ""
        self.positive_patch_ids = set()
        self.total_output_samples = 0

        self.lldata = []
        self.image_info = {}
        self.dlmc_rename_map = dict(DLMC_RENAME_MAP)
        self.dlmc_mapping_excel_path = u"内置映射（已按种类划分表固化）"
        self.dlmc_mapping_loaded = False
        self.unknown_dlmc_values = set()

        self.create_widgets()
        self.update_stride_by_overlap()

    def create_widgets(self):
        main_canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)

        scrollable_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        config_frame = ttk.LabelFrame(scrollable_frame, text=u"基础文件配置", padding=15)
        config_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(config_frame, text=u"影像原图 (.tif):").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(config_frame, textvariable=self.input_path, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(
            config_frame,
            text=u"浏览...",
            command=lambda: self.select_file(self.input_path, "img")
        ).grid(row=0, column=2)

        ttk.Label(config_frame, text=u"标签文件 (.shp):").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(config_frame, textvariable=self.mask_input_path, width=60).grid(row=1, column=1, padx=5)
        ttk.Button(
            config_frame,
            text=u"浏览...",
            command=lambda: self.select_file(self.mask_input_path, "shp_tif")
        ).grid(row=1, column=2)

        ttk.Label(config_frame, text=u"输出根目录:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(config_frame, textvariable=self.output_path, width=60).grid(row=2, column=1, padx=5)
        ttk.Button(config_frame, text=u"浏览...", command=self.select_dir).grid(row=2, column=2)

        ttk.Label(config_frame, text=u"姓名缩写:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(config_frame, textvariable=self.author_abbr_var, width=20).grid(row=3, column=1, sticky="w", padx=5)

        fmt_frame = ttk.LabelFrame(scrollable_frame, text=u"输出格式选择", padding=10)
        fmt_frame.pack(fill="x", padx=10, pady=5)

        ttk.Checkbutton(fmt_frame, text=u"原始 TIF", variable=self.out_tif_var).grid(
            row=0, column=0, sticky="w", padx=10
        )
        ttk.Checkbutton(fmt_frame, text=u"真彩色 JPG", variable=self.out_jpg_true_var).grid(
            row=0, column=1, sticky="w"
        )
        ttk.Label(fmt_frame, text=u"波段(R,G,B):").grid(row=0, column=2, sticky="e")
        ttk.Entry(fmt_frame, textvariable=self.bands_true_var, width=10).grid(
            row=0, column=3, sticky="w", padx=5
        )
        ttk.Checkbutton(fmt_frame, text=u"假彩色 JPG", variable=self.out_jpg_false_var).grid(
            row=0, column=4, sticky="w", padx=10
        )
        ttk.Label(fmt_frame, text=u"波段(NIR,R,G):").grid(row=0, column=5, sticky="e")
        ttk.Entry(fmt_frame, textvariable=self.bands_false_var, width=10).grid(
            row=0, column=6, sticky="w", padx=5
        )
        param_frame = ttk.LabelFrame(scrollable_frame, text=u"切片参数", padding=10)
        param_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(param_frame, text=u"样本尺寸:").grid(row=0, column=0, sticky="w")
        self.combo_patch = ttk.Combobox(
            param_frame,
            textvariable=self.patch_size_var,
            values=self.patch_options,
            width=10,
            state="readonly"
        )
        self.combo_patch.grid(row=0, column=1, sticky="w", padx=(8, 40))
        self.combo_patch.bind("<<ComboboxSelected>>", self.on_patch_change)

        ttk.Label(param_frame, text=u"重叠率:").grid(row=0, column=2, sticky="e", padx=(10, 0))
        self.combo_overlap = ttk.Combobox(
            param_frame,
            textvariable=self.overlap_ratio_var,
            values=self.overlap_options,
            width=10,
            state="readonly"
        )
        self.combo_overlap.grid(row=0, column=3, sticky="w", padx=(8, 40))
        self.combo_overlap.bind("<<ComboboxSelected>>", self.on_overlap_change)

        ttk.Label(param_frame, text=u"步长(自动计算):").grid(row=0, column=4, sticky="e", padx=(10, 0))
        ttk.Entry(param_frame, textvariable=self.stride_var, width=10, state="readonly").grid(
            row=0, column=5, sticky="w", padx=(8, 5)
        )

        run_frame = ttk.Frame(scrollable_frame, padding=15)
        run_frame.pack(fill="x", padx=10)
        self.btn_run = ttk.Button(run_frame, text=u"一键全流程处理", command=self.run_full_process)
        self.btn_run.pack(fill="x", ipady=15)

        log_frame = ttk.LabelFrame(scrollable_frame, text=u"运行日志", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.progress = ttk.Progressbar(scrollable_frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=5, pady=5)
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            state='disabled',
            bg="#f0f0f0",
            font=("Consolas", 9)
        )
        self.log_text.pack(fill="both", expand=True)

    def get_path(self, var):
        p = var.get()
        if sys.version_info[0] < 3 and isinstance(p, unicode):
            return p.encode('mbcs')
        return p

    def get_safe_error_msg(self, e):
        if isinstance(e, unicode):
            return e
        try:
            if sys.version_info[0] < 3:
                return str(e).decode('utf-8')
            return str(e)
        except:
            try:
                if sys.version_info[0] < 3:
                    return str(e).decode('gbk', 'ignore')
                return str(e)
            except:
                return repr(e)

    def to_unicode_safe(self, value):
        try:
            if sys.version_info[0] < 3:
                if isinstance(value, unicode):
                    return value
                if isinstance(value, str):
                    try:
                        return value.decode('utf-8')
                    except:
                        try:
                            return value.decode('gbk')
                        except:
                            return value.decode('latin1', 'ignore')
            else:
                if isinstance(value, bytes):
                    try:
                        return value.decode('utf-8')
                    except:
                        try:
                            return value.decode('gbk')
                        except:
                            return value.decode('latin1', 'ignore')
            return value
        except:
            try:
                return unicode(value)
            except:
                return value

    def normalize_json_obj(self, obj):
        try:
            if isinstance(obj, dict):
                new_d = {}
                for k, v in obj.items():
                    new_d[self.to_unicode_safe(k)] = self.normalize_json_obj(v)
                return new_d
            elif isinstance(obj, list):
                return [self.normalize_json_obj(x) for x in obj]
            elif isinstance(obj, tuple):
                return [self.normalize_json_obj(x) for x in obj]
            elif isinstance(obj, datetime.datetime):
                return obj.isoformat()
            elif isinstance(obj, datetime.date):
                return obj.isoformat()
            else:
                return self.to_unicode_safe(obj)
        except:
            return obj

    def safe_widget_exists(self, widget):
        try:
            return widget is not None and int(widget.winfo_exists()) == 1
        except:
            return False

    def get_clean_int(self, var):
        try:
            val_str = var.get()
            if "x" in val_str:
                return int(val_str.split('x')[0])
            return int(val_str)
        except:
            return 0

    def update_stride_by_overlap(self):
        try:
            val = self.get_clean_int(self.patch_size_var)
            overlap_text = self.overlap_ratio_var.get().strip()
            if overlap_text == u"25%":
                stride_val = max(1, int(round(val * 0.75)))
            else:
                stride_val = max(1, int(round(val * 0.5)))
            self.stride_var.set("{0}x{0}".format(stride_val))
        except:
            pass

    def on_patch_change(self, event):
        self.update_stride_by_overlap()

    def on_overlap_change(self, event):
        self.update_stride_by_overlap()

    def log(self, msg):
        current_time = time.strftime("%H:%M:%S", time.localtime())
        if not isinstance(msg, unicode):
            try:
                if sys.version_info[0] < 3:
                    msg = msg.decode('utf-8')
                else:
                    msg = unicode(msg)
            except:
                try:
                    if sys.version_info[0] < 3:
                        msg = msg.decode('gbk', 'ignore')
                    else:
                        msg = unicode(msg)
                except:
                    msg = repr(msg)
        log_msg = u"[{0}] {1}".format(current_time, msg)
        try:
            if self.safe_widget_exists(getattr(self, 'log_text', None)):
                self.log_text.config(state='normal')
                self.log_text.insert(tk.END, log_msg + "\n")
                self.log_text.see(tk.END)
                self.log_text.config(state='disabled')
            if self.safe_widget_exists(getattr(self, 'root', None)):
                self.root.update()
        except:
            pass

    def select_file(self, var, ftype):
        if ftype == "img":
            ftypes = [("Image Files", "*.tif;*.tiff"), ("All Files", "*.*")]
        elif ftype == "shp_tif":
            ftypes = [("Label Files", "*.shp;*.tif;*.tiff"), ("All Files", "*.*")]
        else:
            ftypes = [("All Files", "*.*")]
        f = filedialog.askopenfilename(filetypes=ftypes)
        if f:
            if sys.version_info[0] < 3 and isinstance(f, str):
                f = f.decode('gbk', 'ignore')
            var.set(f)

    def select_dir(self):
        d = filedialog.askdirectory()
        if d:
            if sys.version_info[0] < 3 and isinstance(d, str):
                d = d.decode('gbk', 'ignore')
            self.output_path.set(d)

    def get_field_name_ignore_case(self, fc, target_name):
        try:
            for f in arcpy.ListFields(fc):
                if f.name.lower() == target_name.lower():
                    return f.name
        except:
            pass
        return None

    def sanitize_folder_name(self, name):
        if name is None:
            name = u"NULL_DLMC"
        try:
            if not isinstance(name, unicode):
                name = unicode(name)
        except:
            name = str(name)

        name = name.strip()
        if name == "":
            name = u"EMPTY_DLMC"

        name = re.sub(u'[\\\\/:*?"<>|]+', u"_", name)
        name = re.sub(u"\\s+", u"_", name)
        if name in [u".", u"..", u""]:
            name = u"EMPTY_DLMC"
        return name



    def sanitize_file_component(self, name):
        if name is None:
            name = u""
        try:
            if not isinstance(name, unicode):
                name = unicode(name)
        except:
            name = str(name)
        name = name.strip()
        name = re.sub(u'[\\/:*?"<>|]+', u"_", name)
        name = re.sub(u"\\s+", u"_", name)
        return name

    def get_source_scene_base_name(self):
        raw_path = self.get_path(self.input_path)
        base = os.path.splitext(os.path.basename(raw_path))[0]
        try:
            if not isinstance(base, unicode):
                base = unicode(base)
        except:
            base = str(base)

        parts = base.split(u"_")
        if len(parts) >= 5 and re.match(u"^\\d{8}$", parts[4]):
            base = u"_".join(parts[:5])
        return self.sanitize_file_component(base)

    def get_satellite_name_from_input(self):
        scene_base = self.get_source_scene_base_name()
        parts = scene_base.split(u"_")
        sat_name = parts[0] if parts else scene_base
        return self.sanitize_folder_name(sat_name)

    def get_author_abbr(self):
        try:
            value = self.author_abbr_var.get()
        except:
            value = u""
        value = self.sanitize_file_component(value)
        return value

    def get_region_name_from_mask_input(self):
        try:
            mask_path = self.mask_input_path.get()
        except:
            mask_path = self.get_path(self.mask_input_path)
        if not mask_path:
            return u"UnknownRegion"

        mask_path = self.to_unicode_safe(mask_path)
        base = os.path.splitext(os.path.basename(mask_path))[0]
        base = self.to_unicode_safe(base)

        scene_base = self.get_source_scene_base_name()
        region_name = base

        scene_prefix = scene_base + u"_"
        if base.startswith(scene_prefix):
            region_name = base[len(scene_prefix):]
        else:
            parts = base.split(u"_")
            if len(parts) > 1:
                region_name = parts[-1]

        region_name = self.sanitize_file_component(region_name)
        if not region_name:
            region_name = u"UnknownRegion"
        return region_name

    def cleanup_preprocessed_output(self, out_root):
        try:
            if not out_root:
                return
            self.current_img = ""
            self.current_mask = ""
            self.current_vector = ""
            self.release_arcpy_locks()
            cleanup_names = [u"0_Preprocessed", u"0 Preprocessed"]
            for name in cleanup_names:
                path = os.path.join(out_root, name)
                if os.path.exists(path):
                    try:
                        self.remove_tree_with_retries(path)
                        self.log(u"已自动删除中间目录: {0}".format(path))
                    except Exception as e:
                        try:
                            self.schedule_delayed_cleanup(path)
                            self.log(u"   已安排后台延迟清理，将在锁释放后继续删除: {0}".format(path))
                        except:
                            pass
                        self.log(u"[警告] 删除中间目录失败: {0} - {1}".format(path, self.get_safe_error_msg(e)))
        except Exception as e:
            self.log(u"[警告] 清理中间目录时发生错误: {0}".format(self.get_safe_error_msg(e)))

    def release_arcpy_locks(self):
        try:
            arcpy.env.workspace = None
        except:
            pass
        try:
            arcpy.env.scratchWorkspace = None
        except:
            pass
        try:
            arcpy.env.snapRaster = None
        except:
            pass
        try:
            arcpy.env.mask = None
        except:
            pass
        try:
            arcpy.env.extent = "MAXOF"
        except:
            pass
        try:
            arcpy.env.outputCoordinateSystem = None
        except:
            pass
        try:
            arcpy.ClearWorkspaceCache_management()
        except:
            pass
        gc.collect()

    def on_rmtree_error(self, func, path, exc_info):
        try:
            os.chmod(path, 0o666)
        except:
            pass
        try:
            func(path)
        except:
            raise exc_info[1]

    def remove_tree_with_retries(self, path, retries=5, delay=0.6):
        last_error = None
        for _ in range(retries):
            try:
                self.release_arcpy_locks()
                self.delete_path_with_arcpy(path)
                shutil.rmtree(path, onerror=self.on_rmtree_error)
                return True
            except Exception as e:
                last_error = e
                time.sleep(delay)
        if last_error is not None:
            raise last_error
        return False

    def delete_path_with_arcpy(self, path):
        if not path or (not os.path.exists(path)):
            return

        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                self.delete_single_path(file_path)
            for name in dirs:
                dir_path = os.path.join(root, name)
                self.delete_single_path(dir_path)

    def delete_single_path(self, path):
        if not path or (not os.path.exists(path)):
            return

        try:
            if arcpy.Exists(path):
                arcpy.Delete_management(path)
                self.release_arcpy_locks()
        except:
            pass

        if os.path.isdir(path):
            try:
                os.rmdir(path)
            except:
                pass
            return

        try:
            os.chmod(path, 0o666)
        except:
            pass

        try:
            os.remove(path)
        except:
            pass

    def schedule_delayed_cleanup(self, path):
        if not path:
            return

        path_u = self.to_unicode_safe(path)
        path_u = os.path.abspath(path_u)

        script = (
            u"$target = {0}; "
            u"$deadline = (Get-Date).AddMinutes(10); "
            u"while ((Get-Date) -lt $deadline) {{ "
            u"if (-not (Test-Path -LiteralPath $target)) {{ exit 0 }}; "
            u"try {{ "
            u"Get-ChildItem -LiteralPath $target -Recurse -Force -ErrorAction SilentlyContinue | "
            u"Where-Object {{ -not $_.PSIsContainer }} | "
            u"ForEach-Object {{ try {{ $_.IsReadOnly = $false }} catch {{}} }}; "
            u"Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction Stop; "
            u"exit 0 "
            u"}} catch {{ Start-Sleep -Seconds 3 }} "
            u"}}; exit 1"
        ).format(self.powershell_single_quote(path_u))

        try:
            subprocess.Popen(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", script],
                close_fds=True
            )
        except TypeError:
            subprocess.Popen(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", script]
            )

    def powershell_single_quote(self, text):
        text = self.to_unicode_safe(text)
        return u"'{0}'".format(text.replace(u"'", u"''"))

    def build_named_output_info(self, mapped_name, patch_id, patch_item=None):
        scene_base = self.get_source_scene_base_name()
        region_name = self.get_region_name_from_mask_input()
        satellite_name = self.get_satellite_name_from_input()
        patch_size = self.get_clean_int(self.patch_size_var)
        author_abbr = self.get_author_abbr()
        row_col_tag = u"R000C000"
        if patch_item is not None:
            try:
                row_idx = int(patch_item.get('row_idx', 0))
            except:
                row_idx = 0
            try:
                col_idx = int(patch_item.get('col_idx', 0))
            except:
                col_idx = 0
            if row_idx > 0 and col_idx > 0:
                row_col_tag = u"R{0}C{1}".format(unicode(row_idx).zfill(3), unicode(col_idx).zfill(3))
        if row_col_tag == u"R000C000":
            try:
                patch_serial = unicode(int(patch_id)).zfill(6)
            except:
                try:
                    patch_serial = unicode(patch_id).zfill(6)
                except:
                    patch_serial = str(patch_id).zfill(6)
            row_col_tag = u"R{0}C000".format(patch_serial)

        category_name = self.sanitize_folder_name(mapped_name)
        scene_base = self.sanitize_file_component(scene_base)
        region_name = self.sanitize_file_component(region_name)
        prefix = self.sanitize_file_component(
            u"{0}_{1}_{2}_{3}_{4}".format(category_name, scene_base, region_name, row_col_tag, patch_size)
        )
        suffix = u""
        if author_abbr:
            suffix = u"_{0}".format(author_abbr)

        return {
            'patches_root_name': u"Patches",
            'category_name': category_name,
            'satellite_name': satellite_name,
            'size_dir_name': u"Size_{0}".format(patch_size),
            'orig_tif_name': prefix + u"_Orig" + suffix + u".tif",
            'true_jpg_name': prefix + u"_True" + suffix + u".jpg",
            'false_jpg_name': prefix + u"_False" + suffix + u".jpg",
            'label_tif_name': prefix + u"_Binary" + suffix + u".tif",
            'geojson_name': prefix + u"_Label" + suffix + u".geojson"
        }

    def copy_file_force(self, src, dst):
        if not src or (not os.path.exists(src)):
            return False
        dst_dir = os.path.dirname(dst)
        if dst_dir and (not os.path.exists(dst_dir)):
            os.makedirs(dst_dir)
        try:
            if os.path.exists(dst):
                os.remove(dst)
        except:
            pass
        shutil.copy(src, dst)
        return True

    def ensure_dlmc_mapping_loaded(self):
        if self.dlmc_mapping_loaded:
            return

        # 这里不再在运行时读取 Excel。
        # 已经按用户提供的“种类划分 xlsx”把映射关系固化到 DLMC_RENAME_MAP 里。
        self.dlmc_rename_map = dict(DLMC_RENAME_MAP)
        self.dlmc_mapping_excel_path = u"内置映射（已按种类划分表固化）"
        self.dlmc_mapping_loaded = True
        self.log(u"   已启用内置种类划分映射，不再运行时读取种类划分 xlsx。")

    def normalize_dlmc_value(self, value):
        if value is None:
            return None
        try:
            if isinstance(value, unicode):
                s = value
            else:
                s = unicode(value)
        except:
            try:
                s = str(value)
                if sys.version_info[0] < 3 and isinstance(s, str):
                    s = s.decode('utf-8', 'ignore')
            except:
                return None

        s = s.strip()
        s = re.sub(u"\\s+", u"", s)
        if s == u"":
            return None
        return s

    def map_dlmc_name(self, dlmc_name):
        self.ensure_dlmc_mapping_loaded()
        key = self.normalize_dlmc_value(dlmc_name)
        if key is None:
            return None
        mapped = self.dlmc_rename_map.get(key)
        if mapped is None:
            if key not in self.unknown_dlmc_values:
                self.unknown_dlmc_values.add(key)
                self.log(u"   [提示] DLMC“{0}”未在种类划分表中出现，按“不考虑”处理。".format(key))
            return DLMC_IGNORE_NAME
        mapped = self.normalize_dlmc_value(mapped)
        if mapped is None:
            return DLMC_IGNORE_NAME
        return mapped

    def copy_shapefile_set(self, src_shp, dst_dir, new_name=None):
        if not os.path.exists(src_shp):
            return False
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

        src_base = os.path.splitext(os.path.basename(src_shp))[0]
        dst_base = src_base if not new_name else os.path.splitext(new_name)[0]

        exts = [".shp", ".shx", ".dbf", ".prj", ".cpg", ".sbn", ".sbx", ".xml"]
        copied = False
        for ext in exts:
            src_file = os.path.splitext(src_shp)[0] + ext
            if os.path.exists(src_file):
                dst_file = os.path.join(dst_dir, dst_base + ext)
                shutil.copy(src_file, dst_file)
                copied = True
        return copied

    def build_where_clause(self, fc, field_name, value):
        fld = arcpy.AddFieldDelimiters(fc, field_name)
        field_obj = None
        for f in arcpy.ListFields(fc):
            if f.name == field_name:
                field_obj = f
                break

        if value is None:
            return u"{0} IS NULL".format(fld)

        if field_obj is not None and field_obj.type in ["String", "Guid", "Date"]:
            try:
                v = unicode(value)
            except:
                v = str(value)
            v = v.replace("'", "''")
            return u"{0} = '{1}'".format(fld, v)
        else:
            return u"{0} = {1}".format(fld, value)

    def build_where_clause_multi(self, fc, field_name, values):
        if values is None:
            return u"1=0"

        try:
            value_list = list(values)
        except:
            value_list = [values]

        if not value_list:
            return u"1=0"

        parts = []
        for v in value_list:
            parts.append(u"({0})".format(self.build_where_clause(fc, field_name, v)))
        return u" OR ".join(parts)

    def _ring_signed_area(self, ring):
        if not ring or len(ring) < 3:
            return 0.0
        area = 0.0
        n = len(ring)
        for i in range(n):
            x1, y1 = ring[i][0], ring[i][1]
            x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
            area += (x1 * y2 - x2 * y1)
        return area / 2.0

    def _close_ring_coords(self, ring):
        coords = []
        for p in ring:
            if p is None:
                continue
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                coords.append([float(p[0]), float(p[1])])
        if len(coords) < 3:
            return []
        if coords[0] != coords[-1]:
            coords.append(coords[0][:])
        if len(coords) < 4:
            return []
        return coords

    def _point_in_ring(self, point, ring):
        if not ring or len(ring) < 4:
            return False
        x, y = point[0], point[1]
        inside = False
        n = len(ring)
        j = n - 1
        for i in range(n):
            xi, yi = ring[i][0], ring[i][1]
            xj, yj = ring[j][0], ring[j][1]
            intersect = ((yi > y) != (yj > y))
            if intersect:
                denom = (yj - yi)
                if denom == 0:
                    denom = 1e-12
                x_cross = (xj - xi) * (y - yi) / float(denom) + xi
                if x < x_cross:
                    inside = not inside
            j = i
        return inside

    def _esri_json_polygon_to_geojson(self, esri_geom):
        rings = esri_geom.get("rings", [])
        if not rings:
            return None

        cleaned = []
        for ring in rings:
            cr = self._close_ring_coords(ring)
            if cr:
                cleaned.append(cr)
        if not cleaned:
            return None

        outers = []
        holes = []
        for ring in cleaned:
            area = self._ring_signed_area(ring)
            if area < 0:
                outers.append([ring])
            else:
                holes.append(ring)

        if not outers:
            biggest = max(cleaned, key=lambda r: abs(self._ring_signed_area(r)))
            outers = [[biggest]]
            holes = [r for r in cleaned if r is not biggest]

        for hole in holes:
            test_pt = hole[0]
            attached = False
            for poly in outers:
                if self._point_in_ring(test_pt, poly[0]):
                    poly.append(hole)
                    attached = True
                    break
            if not attached:
                outers.append([hole])

        if len(outers) == 1:
            return {"type": "Polygon", "coordinates": outers[0]}
        return {"type": "MultiPolygon", "coordinates": [poly for poly in outers]}

    def _esri_json_to_geojson_geom(self, geom_obj):
        if not geom_obj:
            return None
        if "x" in geom_obj and "y" in geom_obj:
            return {"type": "Point", "coordinates": [geom_obj["x"], geom_obj["y"]]}
        if "points" in geom_obj:
            pts = geom_obj.get("points", [])
            if len(pts) == 1:
                return {"type": "Point", "coordinates": pts[0]}
            return {"type": "MultiPoint", "coordinates": pts}
        if "paths" in geom_obj:
            paths = geom_obj.get("paths", [])
            if len(paths) == 1:
                return {"type": "LineString", "coordinates": paths[0]}
            return {"type": "MultiLineString", "coordinates": paths}
        if "rings" in geom_obj:
            return self._esri_json_polygon_to_geojson(geom_obj)
        return None

    def export_geojson(self, in_fc, out_json):
        try:
            if os.path.exists(out_json):
                os.remove(out_json)
        except:
            pass

        try:
            arcpy.FeaturesToJSON_conversion(
                in_fc,
                out_json,
                "FORMATTED",
                "NO_Z_VALUES",
                "NO_M_VALUES",
                "GEOJSON"
            )
            return True
        except:
            pass

        temp_proj = None
        try:
            sr_wgs84 = arcpy.SpatialReference(4326)
            desc = arcpy.Describe(in_fc)
            src_sr = getattr(desc, "spatialReference", None)

            fc_for_export = in_fc
            if src_sr is not None:
                try:
                    src_code = int(src_sr.factoryCode) if src_sr.factoryCode not in [None, 0] else 0
                except:
                    src_code = 0
                if src_code != 4326:
                    temp_dir = arcpy.env.scratchFolder if getattr(arcpy.env, 'scratchFolder', None) else os.path.dirname(out_json)
                    temp_name = "tmp_geojson_proj_{0}.shp".format(str(int(time.time() * 1000))[-10:])
                    temp_proj = os.path.join(temp_dir, temp_name)
                    if arcpy.Exists(temp_proj):
                        arcpy.Delete_management(temp_proj)
                    arcpy.Project_management(in_fc, temp_proj, sr_wgs84)
                    fc_for_export = temp_proj

            fields = []
            skip_types = set(["Geometry", "Blob", "Raster", "GUID"])
            skip_names = set(["Shape", "Shape_Length", "Shape_Area"])
            for f in arcpy.ListFields(fc_for_export):
                if f.type in skip_types:
                    continue
                if f.name in skip_names:
                    continue
                fields.append(f.name)

            cursor_fields = ["SHAPE@JSON"] + fields
            features = []
            cur = None
            try:
                cur = arcpy.da.SearchCursor(fc_for_export, cursor_fields)
                for row in cur:
                    geom_json = row[0]
                    if not geom_json:
                        continue
                    try:
                        esri_geom = json.loads(geom_json)
                    except:
                        continue
                    gj_geom = self._esri_json_to_geojson_geom(esri_geom)
                    if not gj_geom:
                        continue

                    props = {}
                    for idx, fld in enumerate(fields, start=1):
                        val = row[idx]
                        if isinstance(val, datetime.datetime):
                            props[fld] = val.isoformat()
                        elif isinstance(val, datetime.date):
                            props[fld] = val.isoformat()
                        elif hasattr(val, 'item'):
                            try:
                                val = val.item()
                            except:
                                pass
                            if isinstance(val, datetime.datetime):
                                props[fld] = val.isoformat()
                            elif isinstance(val, datetime.date):
                                props[fld] = val.isoformat()
                            else:
                                props[fld] = val
                        else:
                            props[fld] = val

                    features.append({
                        "type": "Feature",
                        "properties": props,
                        "geometry": gj_geom
                    })
            finally:
                if cur is not None:
                    del cur

            collection_name = os.path.splitext(os.path.basename(out_json))[0]
            collection_name = re.sub(r'_Label(?:_[^_]+)?$', '', collection_name)

            fc_obj = {
                "type": "FeatureCollection",
                "name": collection_name,
                "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                "features": features
            }

            fc_obj = self.normalize_json_obj(fc_obj)

            out_json_u = out_json
            try:
                if sys.version_info[0] < 3 and isinstance(out_json, str):
                    out_json_u = out_json.decode('mbcs')
            except:
                out_json_u = out_json

            json_text = json.dumps(fc_obj, ensure_ascii=False, indent=2)
            if sys.version_info[0] < 3 and isinstance(json_text, str):
                try:
                    json_text = json_text.decode('utf-8')
                except:
                    try:
                        json_text = json_text.decode('gbk')
                    except:
                        json_text = unicode(json_text, errors='ignore')

            with io.open(out_json_u, "w", encoding="utf-8") as f:
                f.write(json_text)
            return True
        except Exception as e:
            self.log(u"   [警告] GeoJSON 导出失败 {0}: {1}".format(
                os.path.basename(out_json),
                self.get_safe_error_msg(e)
            ))
            return False
        finally:
            if temp_proj:
                try:
                    if arcpy.Exists(temp_proj):
                        arcpy.Delete_management(temp_proj)
                except:
                    pass

    def save_array_as_jpg_arcpy(self, arr_c3, out_path, ref_raster_props):
        temp_band_files = []
        temp_comp = None
        temp_8u = None
        try:
            data = np.asarray(arr_c3)
            data = self._normalize_array_zero_nodata(data)

            if data.ndim != 3:
                return False

            if data.shape[0] >= 3:
                band_stack = [data[0], data[1], data[2]]
            elif data.shape[2] >= 3:
                band_stack = [data[:, :, 0], data[:, :, 1], data[:, :, 2]]
            else:
                return False

            res_channels = []
            for i in range(3):
                band = np.asarray(band_stack[i], dtype=np.float32)
                finite_mask = np.isfinite(band)
                if not finite_mask.any():
                    res_band = np.zeros_like(band, dtype=np.uint8)
                else:
                    valid = band[finite_mask]
                    p2 = np.percentile(valid, 2)
                    p98 = np.percentile(valid, 98)
                    if p98 - p2 <= 1e-6:
                        vmax = float(valid.max()) if valid.size > 0 else 0.0
                        if vmax <= 1e-6:
                            res_band = np.zeros_like(band, dtype=np.uint8)
                        else:
                            res_band = np.clip((band / vmax) * 255.0, 0, 255).astype(np.uint8)
                    else:
                        res_band = np.clip((band - p2) / (p98 - p2) * 255.0, 0, 255).astype(np.uint8)
                res_channels.append(res_band)

            out_dir = os.path.dirname(out_path)
            if out_dir and (not os.path.exists(out_dir)):
                os.makedirs(out_dir)

            rgb = np.dstack((res_channels[0], res_channels[1], res_channels[2])).astype(np.uint8)

            if HAS_PIL:
                Image.fromarray(rgb, mode="RGB").save(out_path, format="JPEG", quality=95)
                return True

            if HAS_IMAGEIO:
                try:
                    imageio.imwrite(out_path, rgb)
                    if os.path.exists(out_path):
                        return True
                except Exception:
                    pass

            if HAS_CV2:
                try:
                    cv2.imwrite(out_path, rgb[:, :, ::-1], [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                    if os.path.exists(out_path):
                        return True
                except Exception:
                    pass

            if HAS_SCIPY_IMSAVE:
                try:
                    scipy_misc.imsave(out_path, rgb)
                    if os.path.exists(out_path):
                        return True
                except Exception:
                    pass

            lower_left = ref_raster_props['lowerLeft']
            cell_w = ref_raster_props['cell_w']
            cell_h = ref_raster_props['cell_h']
            base_name = os.path.splitext(os.path.basename(out_path))[0]

            for i in range(3):
                temp_band = os.path.join(out_dir, "_jpg_{0}_band{1}.tif".format(base_name, i + 1))
                if arcpy.Exists(temp_band):
                    arcpy.Delete_management(temp_band)
                ras = arcpy.NumPyArrayToRaster(np.asarray(res_channels[i], dtype=np.uint8), lower_left, cell_w, cell_h, value_to_nodata=256)
                ras.save(temp_band)
                temp_band_files.append(temp_band)
                del ras

            temp_comp = os.path.join(out_dir, "_jpg_{0}_comp.tif".format(base_name))
            if arcpy.Exists(temp_comp):
                arcpy.Delete_management(temp_comp)
            arcpy.CompositeBands_management(";".join(temp_band_files), temp_comp)

            temp_8u = os.path.join(out_dir, "_jpg_{0}_8u.tif".format(base_name))
            if arcpy.Exists(temp_8u):
                arcpy.Delete_management(temp_8u)
            arcpy.CopyRaster_management(temp_comp, temp_8u, pixel_type="8_BIT_UNSIGNED", format="TIFF")
            arcpy.CopyRaster_management(temp_8u, out_path, pixel_type="8_BIT_UNSIGNED", format="JPEG")
            return True
        except Exception as e:
            try:
                self.log(u"   [警告] JPG 导出失败 {0}: {1}".format(os.path.basename(out_path), self.get_safe_error_msg(e)))
            except:
                pass
            return False
        finally:
            for p in temp_band_files:
                try:
                    if arcpy.Exists(p):
                        arcpy.Delete_management(p)
                except:
                    pass
            if temp_comp is not None:
                try:
                    if arcpy.Exists(temp_comp):
                        arcpy.Delete_management(temp_comp)
                except:
                    pass
            if temp_8u is not None:
                try:
                    if arcpy.Exists(temp_8u):
                        arcpy.Delete_management(temp_8u)
                except:
                    pass

    def _normalize_array_zero_nodata(self, arr):
        arr = np.asarray(arr)
        if np.issubdtype(arr.dtype, np.floating):
            try:
                arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
            except TypeError:
                arr[np.isnan(arr)] = 0
                arr[np.isinf(arr)] = 0
        return arr

    def _ensure_patch_shape(self, arr, patch_size):
        arr = np.asarray(arr)
        if arr.ndim == 2:
            h, w = arr.shape
            if h == patch_size and w == patch_size:
                return arr
            fixed = np.zeros((patch_size, patch_size), dtype=arr.dtype)
            fixed[:min(h, patch_size), :min(w, patch_size)] = arr[:min(h, patch_size), :min(w, patch_size)]
            return fixed
        elif arr.ndim == 3:
            b, h, w = arr.shape
            if h == patch_size and w == patch_size:
                return arr
            fixed = np.zeros((b, patch_size, patch_size), dtype=arr.dtype)
            fixed[:, :min(h, patch_size), :min(w, patch_size)] = arr[:, :min(h, patch_size), :min(w, patch_size)]
            return fixed
        return arr

    def get_patch_array_fast(self, item, patch_size):
        lower_left = item.get('lowerLeft', arcpy.Point(item['XMin'], item['YMin']))
        try:
            arr = arcpy.RasterToNumPyArray(self.current_img, lower_left, patch_size, patch_size, nodata_to_value=0)
        except TypeError:
            arr = arcpy.RasterToNumPyArray(self.current_img, lower_left, patch_size, patch_size)
        arr = self._normalize_array_zero_nodata(arr)
        arr = self._ensure_patch_shape(arr, patch_size)
        return arr

    def save_patch_tif_from_array(self, arr, out_tif, item):
        ras = None
        try:
            lower_left = item.get('lowerLeft', arcpy.Point(item['XMin'], item['YMin']))
            cell_w = self.image_info['cell_w']
            cell_h = self.image_info['cell_h']
            ras = arcpy.NumPyArrayToRaster(arr, lower_left, cell_w, cell_h)
            ras.save(out_tif)
            try:
                arcpy.DefineProjection_management(out_tif, self.image_info['sp_ref'])
            except:
                pass
            return True
        finally:
            if ras is not None:
                del ras

    def save_patch_tif_direct(self, out_tif, item):
        out_ext = None
        try:
            bbox = item['bbox']
            try:
                arcpy.Clip_management(self.current_img, bbox, out_tif)
            except Exception:
                ext = arcpy.Extent(item['XMin'], item['YMin'], item['XMax'], item['YMax'])
                out_ext = arcpy.sa.ExtractByRectangle(self.current_img, ext, "INSIDE")
                out_ext.save(out_tif)

            self.force_raster_null_to_zero(out_tif)

            try:
                arcpy.DefineProjection_management(out_tif, self.image_info['sp_ref'])
            except:
                pass

            try:
                arcpy.CalculateStatistics_management(out_tif)
            except:
                pass

            return True
        finally:
            if out_ext is not None:
                del out_ext

    def save_binary_mask_from_fc(self, in_fc, out_tif, item, value_field="MASKVAL"):
        raw_tmp = None
        out_ras = None
        try:
            patch_size = self.get_clean_int(self.patch_size_var)
            if patch_size <= 0:
                raise Exception(u"Patch 大小无效。")

            lower_left = item.get('lowerLeft', arcpy.Point(item['XMin'], item['YMin']))
            patch_extent = arcpy.Extent(item['XMin'], item['YMin'], item['XMax'], item['YMax'])
            target_cell = min(abs(self.image_info['cell_w']), abs(self.image_info['cell_h']))

            out_dir = os.path.dirname(out_tif)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)

            base_name = os.path.splitext(os.path.basename(out_tif))[0]
            raw_tmp = os.path.join(out_dir, "_tmp_raw_{0}.tif".format(base_name))
            if arcpy.Exists(raw_tmp):
                arcpy.Delete_management(raw_tmp)

            old_snap = arcpy.env.snapRaster
            old_extent = arcpy.env.extent
            old_outcs = arcpy.env.outputCoordinateSystem

            try:
                arcpy.env.snapRaster = self.current_img
                arcpy.env.outputCoordinateSystem = self.current_img
                arcpy.env.extent = patch_extent

                arcpy.PolygonToRaster_conversion(
                    in_fc,
                    value_field,
                    raw_tmp,
                    "CELL_CENTER",
                    "",
                    target_cell
                )
            finally:
                arcpy.env.snapRaster = old_snap
                arcpy.env.extent = old_extent
                arcpy.env.outputCoordinateSystem = old_outcs

            try:
                arr = arcpy.RasterToNumPyArray(raw_tmp, lower_left, patch_size, patch_size, nodata_to_value=0)
            except TypeError:
                arr = arcpy.RasterToNumPyArray(raw_tmp, lower_left, patch_size, patch_size)

            arr = self._normalize_array_zero_nodata(arr)
            arr = self._ensure_patch_shape(arr, patch_size)

            arr = np.asarray(arr)
            if arr.ndim == 3:
                arr = arr[0]

            arr = np.where(arr > 0, 1, 0).astype(np.uint8)

            out_ras = arcpy.NumPyArrayToRaster(
                arr,
                lower_left,
                self.image_info['cell_w'],
                self.image_info['cell_h']
            )
            out_ras.save(out_tif)

            try:
                arcpy.DefineProjection_management(out_tif, self.image_info['sp_ref'])
            except:
                pass

            try:
                arcpy.CalculateStatistics_management(out_tif)
            except:
                pass

            return True

        except Exception as e:
            self.log(u"   [警告] 二值标签生成失败 {0}: {1}".format(
                os.path.basename(out_tif),
                self.get_safe_error_msg(e)
            ))
            return False

        finally:
            try:
                if out_ras is not None:
                    del out_ras
            except:
                pass
            try:
                if raw_tmp is not None and arcpy.Exists(raw_tmp):
                    arcpy.Delete_management(raw_tmp)
            except:
                pass

    def force_raster_null_to_zero(self, raster_path):
        band_tmp_files = []
        temp_fixed = None

        try:
            temp_dir = os.path.dirname(raster_path)
            base_name = os.path.splitext(os.path.basename(raster_path))[0]
            temp_fixed = os.path.join(temp_dir, "_fixed_{0}.tif".format(base_name))

            if arcpy.Exists(temp_fixed):
                arcpy.Delete_management(temp_fixed)

            desc = arcpy.Describe(raster_path)
            try:
                band_count = int(desc.bandCount)
            except:
                band_count = 1

            if band_count <= 1:
                ras = arcpy.Raster(raster_path)
                fixed_ras = arcpy.sa.Con(arcpy.sa.IsNull(ras), 0, ras)
                fixed_ras.save(temp_fixed)
                del ras, fixed_ras
            else:
                for b in range(1, band_count + 1):
                    band_path = raster_path + "\\Band_{0}".format(b)
                    band_ras = arcpy.Raster(band_path)

                    fixed_band = arcpy.sa.Con(arcpy.sa.IsNull(band_ras), 0, band_ras)

                    band_tmp = os.path.join(
                        temp_dir,
                        "_fixed_{0}_band_{1}.tif".format(base_name, b)
                    )
                    if arcpy.Exists(band_tmp):
                        arcpy.Delete_management(band_tmp)

                    fixed_band.save(band_tmp)
                    band_tmp_files.append(band_tmp)

                    del band_ras, fixed_band

                arcpy.CompositeBands_management(";".join(band_tmp_files), temp_fixed)

            arcpy.CopyRaster_management(temp_fixed, raster_path)
            return True

        except Exception as e:
            self.log(u"   [警告] 输出影像空值归零失败 {0}: {1}".format(
                os.path.basename(raster_path),
                self.get_safe_error_msg(e)
            ))
            return False

        finally:
            try:
                if temp_fixed is not None and arcpy.Exists(temp_fixed):
                    arcpy.Delete_management(temp_fixed)
            except:
                pass

            for f in band_tmp_files:
                try:
                    if arcpy.Exists(f):
                        arcpy.Delete_management(f)
                except:
                    pass

    def cleanup_raster_sidecars(self, raster_path):
        try:
            base = raster_path
            stem = base[:-4] if base.lower().endswith('.tif') else base
            sidecars = [
                base + ".aux.xml",
                base + ".xml",
                base + ".ovr",
                base + ".rrd",
                base + ".aux",
                stem + ".tfw",
                stem + ".tfwx",
                base + ".vat.cpg",
                base + ".vat.dbf",
                base + ".cpg",
                base + ".dbf",
            ]
            for p in sidecars:
                try:
                    if p and os.path.exists(p):
                        os.remove(p)
                except:
                    pass
        except:
            pass

    def smooth_binary_raster_edges(self, in_raster_path, out_raster_path):
        """
        备用平滑方案：比原来的 MajorityFilter 更强，主要用于超采样失败时兜底。
        说明：真正起主要作用的是 make_binary_label_255 里的“2 倍超采样 + MEAN 聚合 + 回落二值化”。
        """
        try:
            ras = arcpy.Raster(in_raster_path)
            work = Con(IsNull(ras), 0, Con(ras > 0, 1, 0))

            try:
                work = Expand(work, 1, [1])
            except:
                pass

            try:
                work = BoundaryClean(work, "ASCEND", "TWO_WAY")
            except:
                pass

            try:
                work = Shrink(work, 1, [1])
            except:
                pass

            try:
                work = BoundaryClean(work, "ASCEND", "TWO_WAY")
            except:
                pass

            work.save(out_raster_path)
            return out_raster_path
        except:
            return in_raster_path


    def make_binary_label_255(self, dominant_fc, patch_item, out_tif, target_cell=None):
        """
        严格按选中的 DLMC 要素生成 0/255 标签：
        - 不做 Expand / Shrink / BoundaryClean 等会把相邻类别揉进来的平滑操作
        - 以原图当前网格作为唯一对齐基准
        - “不考虑”类别天然保持为背景 0
        """
        raw_bin_tif = out_tif + "._raw.tif"
        final_tmp_tif = out_tif + "._f.tif"

        for p in [raw_bin_tif, final_tmp_tif, out_tif]:
            try:
                if arcpy.Exists(p):
                    arcpy.Delete_management(p)
            except:
                pass
            try:
                self.cleanup_raster_sidecars(p)
            except:
                pass

        old_snap = arcpy.env.snapRaster
        old_extent = arcpy.env.extent
        old_outcs = arcpy.env.outputCoordinateSystem
        old_cellsize = arcpy.env.cellSize
        old_pyramid = arcpy.env.pyramid
        try:
            old_stats = arcpy.env.rasterStatistics
        except:
            old_stats = None

        try:
            patch_extent = arcpy.Extent(
                patch_item['XMin'], patch_item['YMin'], patch_item['XMax'], patch_item['YMax']
            )

            arcpy.env.snapRaster = self.current_img
            arcpy.env.cellSize = self.current_img
            arcpy.env.outputCoordinateSystem = self.image_info['sp_ref']
            arcpy.env.extent = patch_extent
            arcpy.env.pyramid = "NONE"
            try:
                arcpy.env.rasterStatistics = "NONE"
            except:
                pass

            arcpy.PolygonToRaster_conversion(
                dominant_fc,
                "BIN",
                raw_bin_tif,
                "CELL_CENTER",
                "",
                self.current_img
            )

            raw_ras = arcpy.Raster(raw_bin_tif)
            out_ras = Con(IsNull(raw_ras), 0, Con(raw_ras > 0, 255, 0))
            out_ras.save(final_tmp_tif)

            try:
                arcpy.CopyRaster_management(final_tmp_tif, out_tif, pixel_type="8_BIT_UNSIGNED")
            except:
                try:
                    if arcpy.Exists(out_tif):
                        arcpy.Delete_management(out_tif)
                except:
                    pass
                arcpy.CopyRaster_management(final_tmp_tif, out_tif, pixel_type="8_BIT_UNSIGNED")

            try:
                arcpy.DefineProjection_management(out_tif, self.image_info['sp_ref'])
            except:
                pass

            try:
                arcpy.CalculateStatistics_management(out_tif)
            except:
                pass

            self.cleanup_raster_sidecars(out_tif)
            return True

        except Exception as e:
            self.log(u"   [警告] 严格标签生成失败 {0}: {1}".format(
                os.path.basename(out_tif),
                self.get_safe_error_msg(e)
            ))
            return False
        finally:
            arcpy.env.snapRaster = old_snap
            arcpy.env.extent = old_extent
            arcpy.env.outputCoordinateSystem = old_outcs
            arcpy.env.cellSize = old_cellsize
            arcpy.env.pyramid = old_pyramid
            try:
                arcpy.env.rasterStatistics = old_stats
            except:
                pass

            for p in [raw_bin_tif, final_tmp_tif]:
                try:
                    if arcpy.Exists(p):
                        arcpy.Delete_management(p)
                except:
                    pass
                try:
                    self.cleanup_raster_sidecars(p)
                except:
                    pass

    def run_full_process(self):

        raw_path = self.get_path(self.input_path)
        mask_path = self.get_path(self.mask_input_path)
        out_root = self.get_path(self.output_path)

        if not raw_path or not os.path.exists(raw_path):
            messagebox.showerror("错误", "原图路径无效。")
            return
        if not mask_path or not os.path.exists(mask_path):
            messagebox.showerror("错误", "标签文件路径无效。")
            return
        if not out_root:
            messagebox.showerror("错误", "输出目录无效。")
            return

        self.btn_run.config(state="disabled")
        self.total_output_samples = 0
        self.log(u"========== 任务开始 ==========")
        self.root.update()

        try:
            if not self.process_phase_0_preprocess():
                raise Exception("预处理阶段失败")

            self.log(u"...[1/6] 计算坐标并生成 Patch 网格...")
            if not self.step_calculate_coords_chunked():
                raise Exception("Step 1 失败")

            self.log(u"...[2/6] 创建 Patch 总索引...")
            if not self.step_create_shapefiles():
                raise Exception("Step 2 失败")

            self.log(u"...[3/6] 先裁标签，识别正样本 Patch...")
            if not self.step_crop_masks():
                raise Exception("Step 3 失败")

            self.log(u"...[4/6] 仅裁正样本影像...")
            if not self.step_crop_images_multiformat():
                raise Exception("Step 4 失败")

            self.log(u"...[5/6] 样本分类与清洗...")
            if not self.step_sort_samples():
                raise Exception("Step 5 失败")

            self.log(u"...[6/6] 正样本按面积占比 >= 10% 的 DLMC 分类，并生成分组影像与二值标签...")
            if not self.step_group_positive_samples_by_dlmc():
                raise Exception("Step 6 失败")

            self.log(u"========== 全部完成！ ==========")
            self.log(u"本次共裁出样本 {0} 个。".format(self.total_output_samples))
            messagebox.showinfo("成功", "处理完毕。\n输出目录: {0}".format(self.output_path.get()))

        except Exception as e:
            err_msg = self.get_safe_error_msg(e)
            self.log(u"!!! 任务中断: {0}".format(err_msg))
            traceback.print_exc()
            messagebox.showerror("错误", u"执行错误:\n{0}".format(err_msg))
        finally:
            try:
                self.cleanup_preprocessed_output(self.get_path(self.output_path))
            except:
                pass
            try:
                if self.safe_widget_exists(getattr(self, 'btn_run', None)):
                    self.btn_run.config(state="normal")
            except:
                pass
            try:
                if self.safe_widget_exists(getattr(self, 'progress', None)):
                    self.progress["value"] = 0
            except:
                pass
            try:
                if self.safe_widget_exists(getattr(self, 'root', None)):
                    self.root.update()
            except:
                pass

    def process_phase_0_preprocess(self):
        self.log(u"正在执行预处理（坐标系统一 + 黑边区域裁剪）...")
        self.root.update()
        try:
            raw_path = self.get_path(self.input_path)
            label_path = self.get_path(self.mask_input_path)
            out_root = self.get_path(self.output_path)

            self.current_vector = ""
            self.current_mask = ""
            self.patch_index_path = ""
            self.positive_patch_ids = set()

            resample_dir = os.path.join(out_root, "0_Preprocessed")
            if not os.path.exists(resample_dir):
                os.makedirs(resample_dir)

            if label_path and label_path.lower().endswith(".shp"):
                temp_input_shp = os.path.join(resample_dir, "input_label_src.shp")
                try:
                    if arcpy.Exists(temp_input_shp):
                        arcpy.Delete_management(temp_input_shp)
                except:
                    pass
                try:
                    self.remove_tree_with_retries(os.path.splitext(temp_input_shp)[0] + ".gdb")
                except:
                    pass
                if not self.copy_shapefile_set(label_path, resample_dir, "input_label_src.shp"):
                    raise Exception(u"无法复制输入 shp，请检查标签文件路径是否有效。")
                label_path = temp_input_shp
                self.log(u"   已复制输入 shp 到中间目录，避免原始中文路径导致 ArcPy 识别失败。")
                self.root.update()

            img_desc = arcpy.Describe(raw_path)
            img_sr = getattr(img_desc, "spatialReference", None)
            lbl_desc = arcpy.Describe(label_path)
            lbl_sr = getattr(lbl_desc, "spatialReference", None)

            target_sr = img_sr
            if target_sr is None or getattr(target_sr, 'name', None) in [None, '', u'Unknown', 'Unknown']:
                if lbl_sr is not None and getattr(lbl_sr, 'name', None) not in [None, '', u'Unknown', 'Unknown']:
                    target_sr = lbl_sr
                else:
                    target_sr = arcpy.SpatialReference(4326)

            self.log(u"   原图坐标系: {0}".format(getattr(img_sr, 'name', u'Unknown')))
            self.log(u"   标签坐标系: {0}".format(getattr(lbl_sr, 'name', u'Unknown')))
            self.log(u"   对齐基准坐标系: {0}".format(getattr(target_sr, 'name', u'Unknown')))
            self.log(u"   为避免样本边缘轻微倾斜，当前版本以原图自身坐标系和像元网格为唯一对齐基准，不再强制重投影到 WGS84。")
            self.root.update()

            if label_path.lower().endswith(".shp"):
                need_project = True
                try:
                    need_project = not lbl_sr or not target_sr or (lbl_sr.factoryCode != target_sr.factoryCode) or (lbl_sr.name != target_sr.name)
                except:
                    need_project = True
                if need_project:
                    self.log(u"   正在将 shp 投影到原图坐标系...")
                    self.root.update()
                    proj_shp = os.path.join(resample_dir, "label_imgsr.shp")
                    arcpy.Project_management(label_path, proj_shp, target_sr)
                    label_path = proj_shp
            else:
                need_project = True
                try:
                    need_project = not lbl_sr or not target_sr or (lbl_sr.factoryCode != target_sr.factoryCode) or (lbl_sr.name != target_sr.name)
                except:
                    need_project = True
                if need_project:
                    self.log(u"   正在将栅格标签投影到原图坐标系...")
                    self.root.update()
                    proj_lbl = os.path.join(resample_dir, "label_imgsr.tif")
                    arcpy.ProjectRaster_management(label_path, proj_lbl, target_sr, "NEAREST")
                    label_path = proj_lbl

            del img_desc
            del lbl_desc

            ras_obj = arcpy.Raster(raw_path)
            cell_x = ras_obj.meanCellWidth
            cell_y = ras_obj.meanCellHeight
            self.log(u"   原图像元大小: {0} x {1}".format(cell_x, cell_y))
            self.root.update()
            del ras_obj

            self.current_img = os.path.join(resample_dir, "image_ref.tif")
            self.log(u"   正在复制原图作为对齐基准，不改变原始像元网格...")
            self.root.update()
            arcpy.CopyRaster_management(raw_path, self.current_img)
            try:
                arcpy.CalculateStatistics_management(self.current_img)
            except:
                pass

            self.log(u"   正在提取原图非纯黑有效区域...")
            self.root.update()

            valid_area_ras = os.path.join(resample_dir, "valid_img_area.tif")
            valid_area_poly = os.path.join(resample_dir, "valid_img_area.shp")
            valid_area_poly_diss = os.path.join(resample_dir, "valid_img_area_diss.shp")

            b1_path = self.current_img + "\\Band_1"
            if not arcpy.Exists(b1_path):
                b1_path = self.current_img
            b1 = arcpy.Raster(b1_path)

            valid_region = arcpy.sa.SetNull(arcpy.sa.IsNull(b1) | (b1 <= 0), 1)
            valid_region.save(valid_area_ras)
            arcpy.RasterToPolygon_conversion(valid_area_ras, valid_area_poly, "NO_SIMPLIFY", "VALUE")
            arcpy.Dissolve_management(valid_area_poly, valid_area_poly_diss)

            arcpy.env.snapRaster = self.current_img
            arcpy.env.outputCoordinateSystem = self.current_img
            arcpy.env.extent = self.current_img

            if label_path.lower().endswith(".shp"):
                self.log(u"   正在按原图有效区域裁剪 shp，只保留重叠部分...")
                self.root.update()

                clipped_shp = os.path.join(resample_dir, "label_overlap.shp")
                arcpy.Clip_analysis(label_path, valid_area_poly_diss, clipped_shp)

                shp_count = int(arcpy.GetCount_management(clipped_shp).getOutput(0))
                if shp_count == 0:
                    self.log(u"   [提示] 裁剪后 shp 与原图有效区域无重叠。")
                else:
                    self.log(u"   裁剪后保留矢量要素数: {0}".format(shp_count))

                self.current_vector = clipped_shp
                self.current_mask = ""

            else:
                self.log(u"   标签为栅格，正在重采样并裁去黑边外区域...")
                self.root.update()

                raw_mask_ras = os.path.join(resample_dir, "temp_raw_mask.tif")
                self.current_mask = os.path.join(resample_dir, "resampled_label.tif")

                arcpy.Resample_management(label_path, raw_mask_ras, self.current_img, "NEAREST")

                raw_ras_obj = arcpy.Raster(raw_mask_ras)
                filled_mask = arcpy.sa.Con(arcpy.sa.IsNull(raw_ras_obj), 0, raw_ras_obj)
                is_invalid = arcpy.sa.IsNull(b1) | (b1 <= 0)
                final_mask = arcpy.sa.Con(is_invalid, 0, filled_mask)
                final_mask.save(self.current_mask)

                del raw_ras_obj, filled_mask, is_invalid, final_mask
                self.current_vector = ""

            del b1, valid_region
            try:
                del img_sr, lbl_sr, target_sr
            except:
                pass
            arcpy.env.extent = "MAXOF"
            arcpy.ClearWorkspaceCache_management()
            gc.collect()
            return True

        except Exception as e:
            self.log(u"预处理错误: {0}".format(self.get_safe_error_msg(e)))
            return False

    def step_calculate_coords_chunked(self):
        try:
            ras_obj = arcpy.Raster(self.current_img)
            cols = ras_obj.width
            rows = ras_obj.height
            extent = ras_obj.extent
            sp_ref = ras_obj.spatialReference
            cell_w = ras_obj.meanCellWidth
            cell_h = ras_obj.meanCellHeight

            self.image_info = {
                'sp_ref': sp_ref,
                'XMin': extent.XMin,
                'YMax': extent.YMax,
                'cell_w': cell_w,
                'cell_h': cell_h,
                'lowerLeft': extent.lowerLeft,
                'rows': rows,
                'cols': cols
            }
            del ras_obj

            num = self.get_clean_int(self.patch_size_var)
            stride = self.get_clean_int(self.stride_var)

            row_steps = list(range(0, rows - num + 1, stride))
            col_steps = list(range(0, cols - num + 1, stride))

            self.lldata = []
            total = len(row_steps) * len(col_steps)
            self.progress["maximum"] = total
            c = 0

            for row_idx, y_px in enumerate(row_steps):
                for col_idx, x_px in enumerate(col_steps):
                    ul_x = extent.XMin + (x_px * cell_w)
                    ul_y = extent.YMax - (y_px * cell_h)

                    p1 = arcpy.Point(ul_x, ul_y)
                    p2 = arcpy.Point(ul_x + num * cell_w, ul_y)
                    p3 = arcpy.Point(ul_x + num * cell_w, ul_y - num * cell_h)
                    p4 = arcpy.Point(ul_x, ul_y - num * cell_h)

                    xmin = ul_x
                    ymin = ul_y - num * cell_h
                    xmax = ul_x + num * cell_w
                    ymax = ul_y

                    bbox_str = "{0:.10f} {1:.10f} {2:.10f} {3:.10f}".format(xmin, ymin, xmax, ymax)

                    self.lldata.append({
                        'points': [p1, p2, p3, p4],
                        'bbox': bbox_str,
                        'XMin': xmin,
                        'YMin': ymin,
                        'XMax': xmax,
                        'YMax': ymax,
                        'row_idx': row_idx + 1,
                        'col_idx': col_idx + 1,
                        'row_px': y_px,
                        'col_px': x_px,
                        'lowerLeft': arcpy.Point(xmin, ymin)
                    })

                    c += 1
                    if c % 2000 == 0:
                        self.progress["value"] = c
                        self.root.update()

            self.log(u"   生成 Patch 总数: {0}".format(len(self.lldata)))
            return True
        except Exception as e:
            self.log(u"Step 1 Error: {0}".format(self.get_safe_error_msg(e)))
            return False

    def step_create_shapefiles(self):
        try:
            if not self.lldata:
                return False

            raw_out = self.get_path(self.output_path)
            vector_dir = os.path.join(raw_out, "Patch_Dataset", "all_patches", "vectors")
            if not os.path.exists(vector_dir):
                os.makedirs(vector_dir)

            self.patch_index_path = os.path.join(vector_dir, "patch_index.shp")

            sp_ref = self.image_info['sp_ref']
            arcpy.CreateFeatureclass_management(vector_dir, "patch_index.shp", "POLYGON", spatial_reference=sp_ref)
            arcpy.AddField_management(self.patch_index_path, "patch_id", "LONG")

            total = len(self.lldata)
            self.progress["maximum"] = total

            cursor = arcpy.da.InsertCursor(self.patch_index_path, ["SHAPE@", "patch_id"])
            try:
                for i, item in enumerate(self.lldata):
                    poly = arcpy.Polygon(arcpy.Array(item['points']), sp_ref)
                    cursor.insertRow([poly, i + 1])

                    if i % 2000 == 0:
                        self.progress["value"] = i
                        self.root.update()
            finally:
                del cursor

            self.progress["value"] = total
            self.root.update()
            self.log(u"   Patch 总索引已创建。")
            return True

        except Exception as e:
            self.log(u"Step 2 Error: {0}".format(self.get_safe_error_msg(e)))
            return False

    def step_crop_masks(self):
        try:
            raw_out = self.get_path(self.output_path)

            # 矢量标签模式：一次总相交，得到正样本 patch_id，并导出正样本 patch shp
            if self.current_vector and arcpy.Exists(self.current_vector):
                out_dir = os.path.join(raw_out, "Patch_Dataset", "all_patches", "vectors_by_patch")
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)

                temp_intersect = os.path.join(out_dir, "_temp_intersect.shp")

                self.log(u"   正在执行矢量标签与 Patch 总索引的一次性相交...")
                self.root.update()

                arcpy.Intersect_analysis([self.current_vector, self.patch_index_path], temp_intersect, "ALL", "", "INPUT")

                patch_id_field = self.get_field_name_ignore_case(temp_intersect, "patch_id")
                if patch_id_field is None:
                    raise Exception(u"相交结果中找不到 patch_id 字段。")

                self.positive_patch_ids = set()
                cursor = None
                try:
                    cursor = arcpy.da.SearchCursor(temp_intersect, [patch_id_field])
                    for row in cursor:
                        try:
                            pid = int(row[0])
                            self.positive_patch_ids.add(pid)
                        except:
                            pass
                finally:
                    if cursor is not None:
                        del cursor

                pos_ids = sorted(list(self.positive_patch_ids))
                self.log(u"   相交后正样本 Patch 数: {0}".format(len(pos_ids)))
                self.progress["maximum"] = max(1, len(pos_ids))

                for i, pid in enumerate(pos_ids):
                    out_name = "patch_{0}.shp".format(pid)
                    where_clause = u"{0} = {1}".format(arcpy.AddFieldDelimiters(temp_intersect, patch_id_field), pid)

                    try:
                        arcpy.FeatureClassToFeatureClass_conversion(
                            temp_intersect,
                            out_dir,
                            out_name,
                            where_clause
                        )
                    except Exception as e:
                        self.log(u"   [警告] 导出 patch shp 失败 {0}: {1}".format(
                            pid, self.get_safe_error_msg(e)
                        ))

                    if i % 100 == 0:
                        self.progress["value"] = i
                        self.root.update()
                    if i % 500 == 0:
                        arcpy.ClearWorkspaceCache_management()
                        gc.collect()

                try:
                    if arcpy.Exists(temp_intersect):
                        arcpy.Delete_management(temp_intersect)
                except:
                    pass

                return True

            # 栅格标签模式：保留旧逻辑
            else:
                out_dir = os.path.join(raw_out, "Patch_Dataset", "all_patches", "masks")
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)

                total = len(self.lldata)
                self.progress["maximum"] = total

                for i, item in enumerate(self.lldata):
                    idx = str(i + 1)
                    out_tif = os.path.join(out_dir, "{0}.tif".format(idx))
                    out_ext = None

                    try:
                        arcpy.Clip_management(self.current_mask, item['bbox'], out_tif)
                    except Exception:
                        try:
                            ext = arcpy.Extent(item['XMin'], item['YMin'], item['XMax'], item['YMax'])
                            out_ext = arcpy.sa.ExtractByRectangle(self.current_mask, ext, "INSIDE")
                            out_ext.save(out_tif)
                        except Exception as e2:
                            self.log(u"   [警告] 掩膜裁剪跳过 {0}: {1}".format(
                                idx, self.get_safe_error_msg(e2)
                            ))
                    finally:
                        if out_ext is not None:
                            del out_ext

                    if i % 50 == 0:
                        self.progress["value"] = i
                        self.root.update()
                    if i % 500 == 0:
                        arcpy.ClearWorkspaceCache_management()
                        gc.collect()
                return True

        except Exception as e:
            self.log(u"Step 3 Error: {0}".format(self.get_safe_error_msg(e)))
            return False

    def step_crop_images_multiformat(self):
        raw_out = self.get_path(self.output_path)
        dir_tif = os.path.join(raw_out, "Patch_Dataset", "all_patches", "images", "tif")
        dir_jpg_true = os.path.join(raw_out, "Patch_Dataset", "all_patches", "images", "jpg_true_color")
        dir_jpg_false = os.path.join(raw_out, "Patch_Dataset", "all_patches", "images", "jpg_false_color")

        img_root = os.path.join(raw_out, "Patch_Dataset", "all_patches", "images")
        if not os.path.exists(img_root):
            os.makedirs(img_root)

        do_tif = self.out_tif_var.get()
        do_true = self.out_jpg_true_var.get()
        do_false = self.out_jpg_false_var.get()

        if do_tif and not os.path.exists(dir_tif):
            os.makedirs(dir_tif)
        if do_true and not os.path.exists(dir_jpg_true):
            os.makedirs(dir_jpg_true)
        if do_false and not os.path.exists(dir_jpg_false):
            os.makedirs(dir_jpg_false)

        def parse_bands(s, default_vals):
            try:
                vals = [int(unicode(x).strip()) - 1 for x in unicode(s).split(',') if unicode(x).strip() != u'']
                vals = [v for v in vals if v >= 0]
                if len(vals) >= 3:
                    return vals[:3]
            except:
                pass
            return list(default_vals)

        b_true = parse_bands(self.bands_true_var.get(), [2, 1, 0])
        b_false = parse_bands(self.bands_false_var.get(), [3, 2, 1])
        patch_size = self.get_clean_int(self.patch_size_var)

        if patch_size <= 0:
            self.log(u"Step 4 Error: Patch 大小无效。")
            return False

        if self.current_vector and arcpy.Exists(self.current_vector):
            target_ids = sorted(list(self.positive_patch_ids))
            if not target_ids:
                self.log(u"   当前无正样本 Patch，跳过影像裁剪。")
                return True
            self.log(u"   Step 4 加速模式：直接从原图窗口读取 NumPy，不再先落盘 Patch 再修复空值。")
        else:
            target_ids = list(range(1, len(self.lldata) + 1))
            self.log(u"   Step 4 加速模式：直接从原图窗口读取 NumPy，裁切全部 Patch。")

        self.progress["maximum"] = max(1, len(target_ids))

        for i, pid in enumerate(target_ids):
            item = self.lldata[pid - 1]
            idx = str(pid)
            arr = None
            props = {
                'lowerLeft': item.get('lowerLeft', arcpy.Point(item['XMin'], item['YMin'])),
                'cell_w': self.image_info['cell_w'],
                'cell_h': self.image_info['cell_h'],
                'sp_ref': self.image_info['sp_ref']
            }

            try:
                arr = self.get_patch_array_fast(item, patch_size)

                if arr is None:
                    self.log(u"   [警告] 影像裁剪跳过 {0}: 读取结果为空".format(idx))
                    continue

                if do_tif:
                    out_tif = os.path.join(dir_tif, "{0}.tif".format(idx))
                    # 保留旧版“直接裁原始栅格”的输出方式，避免 NumPyArrayToRaster
                    # 造成的单波段/灰度显示问题。
                    self.save_patch_tif_direct(out_tif, item)

                if do_true or do_false:
                    if len(arr.shape) == 2:
                        arr_rgb = np.array([arr, arr, arr])
                    else:
                        arr_rgb = arr

                    if do_true:
                        indices = [b for b in b_true if b < arr_rgb.shape[0]]
                        if len(indices) == 3:
                            comp = np.array([arr_rgb[indices[0]], arr_rgb[indices[1]], arr_rgb[indices[2]]])
                            self.save_array_as_jpg_arcpy(
                                comp,
                                os.path.join(dir_jpg_true, "{0}.jpg".format(idx)),
                                props
                            )
                        elif i == 0:
                            self.log(u"   [警告] 真彩色 JPG 波段配置无效或源影像波段不足，当前配置 {0}".format(self.bands_true_var.get()))

                    if do_false:
                        indices = [b for b in b_false if b < arr_rgb.shape[0]]
                        if len(indices) == 3:
                            comp = np.array([arr_rgb[indices[0]], arr_rgb[indices[1]], arr_rgb[indices[2]]])
                            self.save_array_as_jpg_arcpy(
                                comp,
                                os.path.join(dir_jpg_false, "{0}.jpg".format(idx)),
                                props
                            )
                        elif i == 0:
                            self.log(u"   [警告] 假彩色 JPG 波段配置无效或源影像波段不足，当前配置 {0}".format(self.bands_false_var.get()))

                del arr
                arr = None

            except Exception as e:
                self.log(u"   [警告] 影像裁剪跳过 {0}: {1}".format(idx, self.get_safe_error_msg(e)))
            finally:
                if arr is not None:
                    del arr

            if i % 20 == 0:
                self.progress["value"] = i
                self.root.update()
            if i % 300 == 0:
                arcpy.ClearWorkspaceCache_management()
                gc.collect()

        self.progress["value"] = len(target_ids)
        self.root.update()

        if self.current_vector and arcpy.Exists(self.current_vector):
            self.log(u"   仅正样本影像裁剪完成，共 {0} 个 Patch。".format(len(target_ids)))
        else:
            self.log(u"   全部 Patch 影像裁剪完成，共 {0} 个 Patch。".format(len(target_ids)))
        return True


    def step_sort_samples(self):
        try:
            raw_out = self.get_path(self.output_path)
            base = os.path.join(raw_out, "Patch_Dataset")
            samples_root = os.path.join(base, "samples")
            temp_positive_root = os.path.join(base, "_temp_positive_work")

            for d in [samples_root, temp_positive_root]:
                if os.path.exists(d):
                    try:
                        shutil.rmtree(d)
                    except:
                        pass

            if not os.path.exists(samples_root):
                os.makedirs(samples_root)

            # 矢量模式：只整理正样本到临时目录，最终 samples 目录下只保留按类别划分后的结果
            if self.current_vector and arcpy.Exists(self.current_vector):
                pos_vec_src = os.path.join(base, "all_patches", "vectors_by_patch")
                pos_vec_dst = os.path.join(temp_positive_root, "vectors")
                pos_img_base = os.path.join(base, "all_patches", "images")

                for d in [pos_vec_dst]:
                    if not os.path.exists(d):
                        os.makedirs(d)

                if self.out_tif_var.get():
                    d = os.path.join(temp_positive_root, "images", "tif")
                    if not os.path.exists(d):
                        os.makedirs(d)
                if self.out_jpg_true_var.get():
                    d = os.path.join(temp_positive_root, "images", "jpg_true_color")
                    if not os.path.exists(d):
                        os.makedirs(d)
                if self.out_jpg_false_var.get():
                    d = os.path.join(temp_positive_root, "images", "jpg_false_color")
                    if not os.path.exists(d):
                        os.makedirs(d)

                total = len(self.positive_patch_ids)
                self.progress["maximum"] = max(1, total)

                pos_ids = sorted(list(self.positive_patch_ids))
                for i, pid in enumerate(pos_ids):
                    idx = str(pid)
                    shp_src = os.path.join(pos_vec_src, "patch_{0}.shp".format(idx))
                    if os.path.exists(shp_src):
                        self.copy_shapefile_set(shp_src, pos_vec_dst)

                    if self.out_tif_var.get():
                        src = os.path.join(pos_img_base, "tif", idx + ".tif")
                        dst = os.path.join(temp_positive_root, "images", "tif", idx + ".tif")
                        if os.path.exists(src):
                            shutil.copy(src, dst)
                    if self.out_jpg_true_var.get():
                        src = os.path.join(pos_img_base, "jpg_true_color", idx + ".jpg")
                        dst = os.path.join(temp_positive_root, "images", "jpg_true_color", idx + ".jpg")
                        if os.path.exists(src):
                            shutil.copy(src, dst)
                    if self.out_jpg_false_var.get():
                        src = os.path.join(pos_img_base, "jpg_false_color", idx + ".jpg")
                        dst = os.path.join(temp_positive_root, "images", "jpg_false_color", idx + ".jpg")
                        if os.path.exists(src):
                            shutil.copy(src, dst)

                    if i % 50 == 0:
                        self.progress["value"] = i
                        self.root.update()

                self.log(u"Step 5 完成。负样本不再处理；正样本已整理到临时目录，下一步将直接输出到 Patches 分类目录。")
                return True

            # 栅格模式：同样不再保留负样本，只输出正样本到 samples
            else:
                if self.out_tif_var.get():
                    img_dir = os.path.join(base, "all_patches", "images", "tif")
                elif self.out_jpg_true_var.get():
                    img_dir = os.path.join(base, "all_patches", "images", "jpg_true_color")
                else:
                    img_dir = os.path.join(base, "all_patches", "images", "jpg_false_color")

                mask_dir = os.path.join(base, "all_patches", "masks")
                files = glob.glob(os.path.join(mask_dir, "*.tif"))
                filtered_count = 0

                pos_mask_dir = os.path.join(samples_root, "masks")
                if not os.path.exists(pos_mask_dir):
                    os.makedirs(pos_mask_dir)
                if self.out_tif_var.get():
                    d = os.path.join(samples_root, "images", "tif")
                    if not os.path.exists(d):
                        os.makedirs(d)
                if self.out_jpg_true_var.get():
                    d = os.path.join(samples_root, "images", "jpg_true_color")
                    if not os.path.exists(d):
                        os.makedirs(d)
                if self.out_jpg_false_var.get():
                    d = os.path.join(samples_root, "images", "jpg_false_color")
                    if not os.path.exists(d):
                        os.makedirs(d)

                self.progress["maximum"] = len(files)

                for i, mask_p in enumerate(files):
                    fname = os.path.basename(mask_p)
                    ref_img_name = fname if self.out_tif_var.get() else fname.replace(".tif", ".jpg")
                    ref_img_p = os.path.join(img_dir, ref_img_name)
                    is_black = False
                    t_ras = None
                    t_arr = None

                    if os.path.exists(ref_img_p):
                        try:
                            t_ras = arcpy.Raster(ref_img_p)
                            t_arr = arcpy.RasterToNumPyArray(t_ras, nodata_to_value=0)
                            if np.max(t_arr) <= 5:
                                is_black = True
                        except:
                            pass
                        finally:
                            if t_ras is not None:
                                del t_ras
                            if t_arr is not None:
                                del t_arr
                    else:
                        is_black = True

                    if is_black:
                        filtered_count += 1
                        continue

                    try:
                        res_max = arcpy.GetRasterProperties_management(mask_p, "MAXIMUM")
                        is_neg = (float(res_max.getOutput(0)) < 1.0)
                    except:
                        is_neg = True

                    if is_neg:
                        continue

                    shutil.copy(mask_p, os.path.join(samples_root, "masks", fname))
                    base_name = fname.replace(".tif", "")
                    if self.out_tif_var.get():
                        src = os.path.join(base, "all_patches", "images", "tif", fname)
                        if os.path.exists(src):
                            shutil.copy(src, os.path.join(samples_root, "images", "tif", fname))
                    if self.out_jpg_true_var.get():
                        src = os.path.join(base, "all_patches", "images", "jpg_true_color", base_name + ".jpg")
                        if os.path.exists(src):
                            shutil.copy(src, os.path.join(samples_root, "images", "jpg_true_color", base_name + ".jpg"))
                    if self.out_jpg_false_var.get():
                        src = os.path.join(base, "all_patches", "images", "jpg_false_color", base_name + ".jpg")
                        if os.path.exists(src):
                            shutil.copy(src, os.path.join(samples_root, "images", "jpg_false_color", base_name + ".jpg"))

                    if i % 50 == 0:
                        self.progress["value"] = i
                        self.root.update()

                self.log(u"Step 5 完成。已过滤 {0} 张全黑图片；负样本不再输出，仅保留正样本。".format(filtered_count))
                return True

        except Exception as e:
            self.log(u"Step 5 Error: {0}".format(self.get_safe_error_msg(e)))
            return False



    def step_group_positive_samples_by_dlmc(self):
        try:
            self.ensure_dlmc_mapping_loaded()
            raw_out = self.get_path(self.output_path)
            base = os.path.join(raw_out, "Patch_Dataset")

            if self.current_vector and arcpy.Exists(self.current_vector):
                temp_positive_root = os.path.join(base, "_temp_positive_work")
                pos_vec_dir = os.path.join(temp_positive_root, "vectors")
                if not os.path.exists(pos_vec_dir):
                    self.log(u"   未找到正样本矢量目录，跳过 DLMC 归类。")
                    return True

                shp_files = glob.glob(os.path.join(pos_vec_dir, "*.shp"))
                if not shp_files:
                    self.log(u"   正样本中没有 shp 文件，跳过 DLMC 归类。")
                    return True

                patches_root = os.path.join(raw_out, u"Patches")
                if not os.path.exists(patches_root):
                    os.makedirs(patches_root)

                temp_root = os.path.join(base, "_temp_grouped_work")
                if os.path.exists(temp_root):
                    try:
                        shutil.rmtree(temp_root)
                    except:
                        pass
                os.makedirs(temp_root)

                pos_img_tif_dir = os.path.join(temp_positive_root, "images", "tif")
                pos_img_true_dir = os.path.join(temp_positive_root, "images", "jpg_true_color")
                pos_img_false_dir = os.path.join(temp_positive_root, "images", "jpg_false_color")
                target_cell = min(abs(self.image_info['cell_w']), abs(self.image_info['cell_h']))
                area_ratio_threshold = 0.10
                self.progress["maximum"] = len(shp_files)

                total_generated = 0
                total_multi_patch = 0
                total_skipped_ignored = 0

                try:
                    for i, shp_p in enumerate(shp_files):
                        shp_name = os.path.basename(shp_p)
                        base_no_ext = os.path.splitext(shp_name)[0]
                        idx_str = base_no_ext.replace("patch_", "")

                        try:
                            patch_id = int(idx_str)
                        except:
                            self.log(u"   [警告] 无法解析 patch id: {0}".format(shp_name))
                            continue

                        if patch_id < 1 or patch_id > len(self.lldata):
                            self.log(u"   [警告] patch id 越界: {0}".format(shp_name))
                            continue

                        dlmc_field = self.get_field_name_ignore_case(shp_p, "DLMC")
                        if dlmc_field is None:
                            self.log(u"   [警告] {0} 找不到 DLMC 字段，跳过。".format(shp_name))
                            continue

                        mapped_area_dict = {}
                        mapped_original_dict = {}
                        ignored_area = 0.0

                        cursor = None
                        try:
                            cursor = arcpy.da.SearchCursor(shp_p, [dlmc_field, "SHAPE@AREA"])
                            for row in cursor:
                                original_key = self.normalize_dlmc_value(row[0])
                                area_val = row[1] if row[1] is not None else 0.0
                                area_val = float(area_val)

                                mapped_name = self.map_dlmc_name(original_key)
                                if mapped_name == DLMC_IGNORE_NAME:
                                    ignored_area += area_val
                                    continue

                                if mapped_name not in mapped_area_dict:
                                    mapped_area_dict[mapped_name] = 0.0
                                    mapped_original_dict[mapped_name] = set()
                                mapped_area_dict[mapped_name] += area_val
                                mapped_original_dict[mapped_name].add(original_key)
                        finally:
                            if cursor is not None:
                                del cursor

                        if ignored_area > 0:
                            total_skipped_ignored += 1

                        if not mapped_area_dict:
                            self.log(u"   [提示] {0} 中可参与处理的类别为空（可能全部映射为“不考虑”），已跳过。".format(shp_name))
                            continue

                        total_area = sum([v for v in mapped_area_dict.values() if v is not None])
                        if total_area <= 0:
                            self.log(u"   [警告] {0} 的有效面积总和为 0，跳过。".format(shp_name))
                            continue

                        qualified_items = []
                        for mapped_name, merged_area in mapped_area_dict.items():
                            ratio = float(merged_area) / float(total_area)
                            if ratio >= area_ratio_threshold:
                                orig_list = sorted(list(mapped_original_dict.get(mapped_name, [])))
                                qualified_items.append((mapped_name, merged_area, ratio, orig_list))

                        qualified_items = sorted(
                            qualified_items,
                            key=lambda x: (-x[2], -x[1], u"" if x[0] is None else self.to_unicode_safe(x[0]))
                        )

                        if not qualified_items:
                            dominant_item = max(mapped_area_dict.items(), key=lambda x: x[1])
                            dom_ratio = float(dominant_item[1]) / float(total_area)
                            self.log(u"   [提示] {0} 中没有映射后类别占比达到 10%，已跳过。主导类别为 {1} ({2:.2f}%)。".format(
                                shp_name,
                                u"<None>" if dominant_item[0] is None else dominant_item[0],
                                dom_ratio * 100.0
                            ))
                            continue

                        if len(qualified_items) > 1:
                            total_multi_patch += 1

                        item = self.lldata[patch_id - 1]

                        for q_idx, (mapped_name, merged_area, ratio, orig_list) in enumerate(qualified_items):
                            out_info = self.build_named_output_info(mapped_name, idx_str, item)

                            category_dir = os.path.join(patches_root, out_info['category_name'])
                            satellite_dir = os.path.join(category_dir, out_info['satellite_name'])
                            size_dir = os.path.join(satellite_dir, out_info['size_dir_name'])
                            orig_dir = os.path.join(size_dir, "Image_Orig")
                            true_dir = os.path.join(size_dir, "Image_TrueColor")
                            false_dir = os.path.join(size_dir, "Image_FalseColor")
                            label_dir = os.path.join(size_dir, "Label_Binary")
                            geojson_dir = os.path.join(size_dir, "Label_GeoJSON")

                            required_dirs = [label_dir, geojson_dir]
                            if self.out_tif_var.get():
                                required_dirs.append(orig_dir)
                            if self.out_jpg_true_var.get():
                                required_dirs.append(true_dir)
                            if self.out_jpg_false_var.get():
                                required_dirs.append(false_dir)
                            for d in required_dirs:
                                if not os.path.exists(d):
                                    os.makedirs(d)

                            if self.out_tif_var.get():
                                src = os.path.join(pos_img_tif_dir, idx_str + ".tif")
                                dst = os.path.join(orig_dir, out_info['orig_tif_name'])
                                if self.copy_file_force(src, dst):
                                    self.cleanup_raster_sidecars(dst)

                            if self.out_jpg_true_var.get():
                                src = os.path.join(pos_img_true_dir, idx_str + ".jpg")
                                dst = os.path.join(true_dir, out_info['true_jpg_name'])
                                self.copy_file_force(src, dst)

                            if self.out_jpg_false_var.get():
                                src = os.path.join(pos_img_false_dir, idx_str + ".jpg")
                                dst = os.path.join(false_dir, out_info['false_jpg_name'])
                                self.copy_file_force(src, dst)

                            temp_name = "dlmc_{0}_{1}.shp".format(idx_str, q_idx + 1)
                            temp_path = os.path.join(temp_root, temp_name)
                            try:
                                if arcpy.Exists(temp_path):
                                    arcpy.Delete_management(temp_path)
                            except:
                                pass

                            where_clause = self.build_where_clause_multi(shp_p, dlmc_field, orig_list)
                            arcpy.FeatureClassToFeatureClass_conversion(
                                shp_p,
                                temp_root,
                                temp_name,
                                where_clause
                            )

                            class_count = int(arcpy.GetCount_management(temp_path).getOutput(0))
                            if class_count == 0:
                                self.log(u"   [警告] {0} 的映射类别 {1} 提取后为空，跳过。".format(
                                    shp_name,
                                    u"<None>" if mapped_name is None else mapped_name
                                ))
                                continue

                            if "BIN" not in [f.name for f in arcpy.ListFields(temp_path)]:
                                arcpy.AddField_management(temp_path, "BIN", "SHORT")

                            ucur = None
                            try:
                                ucur = arcpy.da.UpdateCursor(temp_path, ["BIN"])
                                for row in ucur:
                                    row[0] = 1
                                    ucur.updateRow(row)
                            finally:
                                if ucur is not None:
                                    del ucur

                            out_bin_tif = os.path.join(label_dir, out_info['label_tif_name'])
                            self.make_binary_label_255(temp_path, item, out_bin_tif, target_cell)
                            total_generated += 1

                            out_json = os.path.join(geojson_dir, out_info['geojson_name'])
                            ok = self.export_geojson(temp_path, out_json)
                            if (not ok) or (not os.path.exists(out_json)):
                                self.log(u"   [警告] {0} 的 GeoJSON 未成功生成。".format(out_info['geojson_name']))

                        if i % 20 == 0:
                            self.progress["value"] = i
                            self.root.update()
                        if i % 200 == 0:
                            arcpy.ClearWorkspaceCache_management()
                            gc.collect()
                finally:
                    try:
                        shutil.rmtree(temp_root)
                    except:
                        pass
                    try:
                        shutil.rmtree(temp_positive_root)
                    except:
                        pass

                try:
                    if os.path.exists(base):
                        shutil.rmtree(base)
                except:
                    pass

                self.total_output_samples = total_generated
                self.progress["value"] = len(shp_files)
                self.root.update()
                self.log(u"Step 6 完成。已按 RS_Samples_CBG/Patches/类别/卫星名/Size_尺寸/数据类型 结构输出。")
                self.log(u"   共生成 {0} 个类别标签；其中 {1} 个 patch 同时命中多个映射后类别。".format(total_generated, total_multi_patch))
                self.log(u"   有 {0} 个 patch 含有被映射为“不考虑”的类别，这些类别已跳过。".format(total_skipped_ignored))
                return True

            else:
                self.log(u"   当前为栅格标签模式，跳过 DLMC 归类。")
                return True

        except Exception as e:
            self.log(u"Step 6 Error: {0}".format(self.get_safe_error_msg(e)))
            return False


if __name__ == "__main__":
    root = tk.Tk()
    app = GeoCutterDynamicField(root)
    root.mainloop()
