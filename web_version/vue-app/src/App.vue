<template>
  <div class="app-container" :data-theme="theme">
    <header class="app-header">
      <div class="header-content">
        <div class="logo-section">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 6v6l4 2"/>
            </svg>
          </div>
          <div class="logo-text">
            <h1>遥感样本制作工具</h1>
            <p class="subtitle">Remote Sensing Sample Tool</p>
          </div>
        </div>
        <div class="header-right">
          <div class="header-status" :class="status">
            <span class="status-dot"></span>
            <span>{{ statusText }}</span>
          </div>
          <button class="theme-btn" @click="toggleTheme" :title="theme === 'dark' ? '切换亮色' : '切换暗色'">
            <svg v-if="theme === 'dark'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
            </svg>
            <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <main class="main-content">
      <section class="config-section">
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              <span>文件配置</span>
            </div>
          </div>
          <div class="panel-body">
            <div class="field">
              <label class="field-label">影像原图 (TIFF)</label>
              <div class="file-drop" :class="{ 'has-file': imageFile }">
                <input type="file" id="imageFile" accept=".tif,.tiff" @change="onImageSelect" class="file-input" ref="imageInput">
                <label for="imageFile" class="file-drop-label">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/></svg>
                  <span>{{ imageFile ? imageFile.name : '点击选择 TIFF 文件' }}</span>
                </label>
              </div>
              <p class="field-hint" v-if="imageFile">{{ formatFileSize(imageFile.size) }}</p>
            </div>
            <div class="field">
              <label class="field-label">标签文件 (SHP / TIFF)</label>
              <div class="file-drop" :class="{ 'has-file': labelFiles.length > 0 }">
                <input type="file" id="labelFile" accept=".shp,.shx,.dbf,.prj,.cpg,.sbn,.sbx,.xml,.tif,.tiff" @change="onLabelSelect" class="file-input" multiple ref="labelInput">
                <label for="labelFile" class="file-drop-label">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/></svg>
                  <span>{{ labelFileDisplay }}</span>
                </label>
              </div>
              <div class="file-tags" v-if="labelFiles.length > 0">
                <span class="file-tag" v-for="(f, idx) in labelFiles" :key="idx">{{ f.name }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>
              <span>参数设置</span>
            </div>
          </div>
          <div class="panel-body">
            <div class="field-row">
              <div class="field">
                <label class="field-label">姓名缩写</label>
                <input type="text" v-model="authorAbbr" placeholder="ZS" maxlength="10" class="text-input">
              </div>
              <div class="field">
                <label class="field-label">样本尺寸</label>
                <select v-model="patchSize" class="select-input">
                  <option value="128x128">128 × 128</option>
                  <option value="256x256">256 × 256</option>
                  <option value="512x512">512 × 512</option>
                </select>
              </div>
              <div class="field">
                <label class="field-label">重叠率</label>
                <select v-model="overlapRatio" class="select-input">
                  <option value="25%">25%</option>
                  <option value="50%">50%</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
              <span>输出格式</span>
            </div>
          </div>
          <div class="panel-body">
            <div class="checkbox-row">
              <label class="check-chip" :class="{ active: outputFormats.tif }">
                <input type="checkbox" v-model="outputFormats.tif" class="hidden-check">
                <span>原始 TIFF</span>
              </label>
              <label class="check-chip" :class="{ active: outputFormats.jpg_true }">
                <input type="checkbox" v-model="outputFormats.jpg_true" class="hidden-check">
                <span>真彩色 JPG</span>
              </label>
              <label class="check-chip" :class="{ active: outputFormats.jpg_false }">
                <input type="checkbox" v-model="outputFormats.jpg_false" class="hidden-check">
                <span>假彩色 JPG</span>
              </label>
            </div>
            <div class="divider"></div>
            <div class="field-row">
              <div class="field">
                <label class="field-label">真彩色 (R,G,B)</label>
                <input type="text" v-model="bandsTrue" placeholder="3,2,1" class="text-input small">
              </div>
              <div class="field">
                <label class="field-label">假彩色 (NIR,R,G)</label>
                <input type="text" v-model="bandsFalse" placeholder="4,3,2" class="text-input small">
              </div>
            </div>
          </div>
        </div>

        <div class="action-bar">
          <button class="process-btn" @click="startProcess" :disabled="!canStart" :class="{ processing: status === 'processing' }">
            <span class="btn-icon">{{ status === 'processing' ? '⏳' : '🚀' }}</span>
            <span>{{ status === 'processing' ? '处理中...' : '一键全流程处理' }}</span>
            <div v-if="status === 'processing'" class="btn-spinner"></div>
          </button>
        </div>
      </section>

      <section class="result-section">
        <div class="panel status-panel" :class="status">
          <div class="panel-header">
            <div class="panel-title">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
              <span>处理状态</span>
            </div>
            <span class="status-badge" :class="status">{{ statusText }}</span>
          </div>
          <div class="panel-body" v-if="status !== 'idle'">
            <div class="progress-area" v-if="status === 'processing'">
              <div class="progress-track">
                <div class="progress-fill" :style="{ width: displayProgress + '%' }"></div>
              </div>
              <div class="progress-right">
                <span class="progress-pct">{{ displayProgress }}<small>%</small></span>
                <button class="stop-btn" @click="stopProcess">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="12" height="16"/><rect x="4" y="6" width="16" height="12"/></svg>
                  <span>停止</span>
                </button>
              </div>
            </div>
            
            <p class="status-message">{{ progressMessage }}</p>
          </div>
          <div class="panel-idle" v-else>
            <div class="idle-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            </div>
            <p>请选择文件并配置参数后开始处理</p>
          </div>
        </div>

        <div class="panel log-panel">
          <div class="panel-header">
            <div class="panel-title">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
              <span>运行日志</span>
            </div>
            <button class="ghost-btn" @click="clearLogs" v-if="logs.length > 0">清空</button>
          </div>
          <div class="log-terminal" ref="logContainer">
            <template v-if="logs.length > 0">
              <div v-for="(log, i) in logs" :key="i" class="log-row" :class="log.type">
                <span class="log-ts">{{ log.time }}</span>
                <span class="log-type">[{{ log.type.toUpperCase() }}]</span>
                <span class="log-msg">{{ log.message }}</span>
              </div>
            </template>
            <div class="log-empty" v-else>
              <span>—</span>
              <p>暂无日志，等待任务启动</p>
            </div>
          </div>
        </div>

        <div class="panel download-panel">
          <div class="success-icon" :class="{ disabled: status !== 'completed' }">
            <svg v-if="status === 'completed'" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            <svg v-else width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          </div>
          <h3 class="success-title">{{ status === 'completed' ? '处理完成' : '等待任务' }}</h3>
          <p class="success-desc">{{ status === 'completed' ? '任务已成功完成，点击下方下载结果' : '请先上传文件并启动任务' }}</p>
          
          <div v-if="downloadInfo" class="download-info">
            <div class="info-item">
              <span class="info-label">文件大小</span>
              <span class="info-value">{{ formatFileSize(downloadInfo.file_size) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">文件名</span>
              <span class="info-value">{{ downloadInfo.file_name }}</span>
            </div>
          </div>

          <div v-if="downloading" class="download-progress">
            <div class="progress-track">
              <div class="progress-fill" :style="{ width: downloadProgress + '%' }"></div>
            </div>
            <span class="progress-text">{{ downloadProgress }}%</span>
          </div>

          <div v-if="downloadError" class="download-error">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <span>{{ downloadError }}</span>
            <button class="retry-btn" @click="handleDownload">重试</button>
          </div>

          <button v-else class="download-btn" @click="handleDownload" :disabled="downloading || status !== 'completed'">
            <svg v-if="!downloading" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <svg v-else class="spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.2-6.32"/><path d="M12 3v9"/></svg>
            <span>{{ downloading ? '下载中...' : '下载结果文件' }}</span>
          </button>
        </div>
      </section>
    </main>

    <footer class="app-footer">
      <p>遥感样本制作工具 v1.0.0</p>
    </footer>

    <div class="modal-overlay" v-if="showCompleteModal" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="20 6 9 17 4 12"/></svg>
        </div>
        <h3 class="modal-title">任务已完成</h3>
        <p class="modal-desc">处理已成功完成，您可以下载结果文件</p>
        <div class="modal-actions">
          <button class="modal-btn modal-btn-secondary" @click="closeModal">关闭</button>
          <button class="modal-btn modal-btn-primary" @click="closeModal">完成</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'

const imageFile = ref(null)
const labelFiles = ref([])
const authorAbbr = ref('')
const outputFormats = ref({ tif: true, jpg_true: true, jpg_false: true })
const bandsTrue = ref('3,2,1')
const bandsFalse = ref('4,3,2')
const patchSize = ref('128x128')
const overlapRatio = ref('25%')

const status = ref('idle')
const progress = ref(0)
const displayProgress = ref(0)
const progressMessage = ref('')
const logs = ref([])
const taskId = ref('')
const logContainer = ref(null)
const imageInput = ref(null)
const labelInput = ref(null)

const theme = ref('dark')
const showCompleteModal = ref(false)
const downloadInfo = ref(null)
const downloading = ref(false)
const downloadProgress = ref(0)
const downloadError = ref(null)
const taskCompleted = ref(false)
let statusTimer = null
let logTimer = null
let lastLogMessage = ''
let progressTimer = null

function startProgressAnimation() {
  if (progressTimer) clearInterval(progressTimer)
  
  if (displayProgress.value >= progress.value) {
    if (displayProgress.value >= 100 && showCompleteModal.value === false && status.value === 'completed') {
      setTimeout(() => { showCompleteModal.value = true }, 500)
    }
    return
  }
  
  const step = Math.max(1, Math.ceil((progress.value - displayProgress.value) / 50))
  
  progressTimer = setInterval(() => {
    if (displayProgress.value < progress.value) {
      displayProgress.value = Math.min(displayProgress.value + step, progress.value)
    } else {
      clearInterval(progressTimer)
      progressTimer = null
    }
    
    if (displayProgress.value >= 100 && showCompleteModal.value === false && status.value === 'completed') {
      clearInterval(progressTimer)
      progressTimer = null
      setTimeout(() => { showCompleteModal.value = true }, 500)
    }
  }, 50)
}

const downloadUrl = computed(() => `/api/download/${taskId.value}`)

const canStart = computed(() => {
  return imageFile.value && labelFiles.value.length > 0 && status.value !== 'processing'
})

const labelFileDisplay = computed(() => {
  if (labelFiles.value.length === 0) return '点击选择文件'
  if (labelFiles.value.length === 1) return labelFiles.value[0].name
  const shpFile = labelFiles.value.find(f => f.name.toLowerCase().endsWith('.shp'))
  return (shpFile ? shpFile.name : labelFiles.value[0].name) + ` (+${labelFiles.value.length - 1} 个)`
})

const statusText = computed(() => {
  const t = { idle: '就绪', processing: '处理中', completed: '已完成', error: '出错' }
  return t[status.value] || '未知'
})

function initTheme() {
  const saved = localStorage.getItem('rtool-theme')
  if (saved === 'light' || saved === 'dark') { theme.value = saved; return }
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) { theme.value = 'light' }
}

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  localStorage.setItem('rtool-theme', theme.value)
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024, s = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + s[i]
}

function onImageSelect(e) { imageFile.value = e.target.files[0] }
function onLabelSelect(e) { labelFiles.value = Array.from(e.target.files) }

function cleanMessage(message) {
  return message.replace(/^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\s*/, '')
}

function addLog(type, message) {
  const now = new Date()
  const time = now.toLocaleTimeString('zh-CN', { hour12: false })
  logs.value.push({ type, message, time })
  nextTick(() => { if (logContainer.value) logContainer.value.scrollTop = logContainer.value.scrollHeight })
}

function clearLogs() { logs.value = [] }

function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16)
  })
}

async function startProcess() {
  if (!canStart.value) return
  taskId.value = generateUUID()
  status.value = 'processing'
  progress.value = 0
  displayProgress.value = 0
  progressMessage.value = '准备上传文件...'
  logs.value = []
  lastLogMessage = ''
  addLog('info', `任务ID: ${taskId.value}`)
  addLog('info', '开始上传文件...')
  try {
    const fd = new FormData()
    fd.append('task_id', taskId.value)
    fd.append('image_file', imageFile.value)
    for (const f of labelFiles.value) fd.append('label_files', f)
    const upRes = await fetch('/api/upload', { method: 'POST', body: fd })
    if (!upRes.ok) throw new Error('文件上传失败')
    addLog('success', '文件上传完成')
    progress.value = 20
    startProgressAnimation()
    progressMessage.value = '文件上传完成，正在处理...'
    const pRes = await fetch('/api/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        task_id: taskId.value, patch_size: patchSize.value,
        overlap_ratio: overlapRatio.value, author_abbr: authorAbbr.value,
        output_formats: outputFormats.value,
        bands_true: bandsTrue.value, bands_false: bandsFalse.value
      })
    })
    if (!pRes.ok) throw new Error('处理启动失败')
    addLog('info', '处理已启动，正在等待完成...')
    statusTimer = setInterval(checkStatus, 5000)
    logTimer = setInterval(fetchLogs, 3000)
  } catch (err) {
    addLog('error', '错误: ' + err.message)
    status.value = 'error'
    progressMessage.value = '处理失败: ' + err.message
  }
}

async function checkStatus() {
  if (!taskId.value) return
  try {
    const res = await fetch(`/api/status/${taskId.value}`)
    if (res.status === 404) { clearInterval(statusTimer); clearInterval(logTimer); status.value = 'idle'; taskId.value = ''; addLog('warn', '任务不存在，已停止轮询。'); return }
    const data = await res.json()
    if (data.progress > 0 && data.progress >= progress.value) {
      progress.value = data.progress
      startProgressAnimation()
    }
    if (data.log_message && data.log_message !== lastLogMessage) {
      lastLogMessage = data.log_message
      addLog('info', data.log_message)
      progressMessage.value = cleanMessage(data.log_message)
    }
    if (data.status === 'completed') {
      clearInterval(statusTimer);
      clearInterval(logTimer);
      status.value = 'completed';
      progress.value = 100;
      taskCompleted.value = true;
      if (displayProgress.value < 100) {
        startProgressAnimation()
      } else {
        setTimeout(() => { showCompleteModal.value = true }, 500)
      }
      addLog('success', '处理完成！');
      await fetchDownloadInfo();
    }
    else if (data.status === 'error') { clearInterval(statusTimer); clearInterval(logTimer); status.value = 'error'; addLog('error', '处理出错: ' + data.message) }
  } catch (e) { console.error('Status check failed:', e) }
}

async function fetchDownloadInfo() {
  if (!taskId.value) return
  try {
    const res = await fetch(`/api/download-info/${taskId.value}`)
    if (res.ok) {
      downloadInfo.value = await res.json()
    }
  } catch (e) {
    console.error('Failed to fetch download info:', e)
  }
}

function handleDownloadClick() {
  if (!taskId.value || downloading.value) return
  
  if (status.value === 'processing' && !taskCompleted.value) {
    addLog('warn', '任务未完成，请等待处理结束后再下载')
    return
  }
  
  handleDownload()
}

async function handleDownload() {
  if (!taskId.value || downloading.value) return
  
  downloading.value = true
  downloadError.value = null
  downloadProgress.value = 0
  
  try {
    const url = `/api/download/${taskId.value}`
    const response = await fetch(url)
    
    if (!response.ok) {
      throw new Error(`下载失败: ${response.status}`)
    }
    
    const contentLength = response.headers.get('Content-Length')
    const total = contentLength ? parseInt(contentLength) : 0
    let loaded = 0
    
    const reader = response.body.getReader()
    const chunks = []
    
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) break
      
      chunks.push(value)
      loaded += value.length
      
      if (total > 0) {
        downloadProgress.value = Math.round((loaded / total) * 100)
      }
    }
    
    const blob = new Blob(chunks)
    const downloadUrl = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = downloadInfo.value?.file_name || `遥感样本_${taskId.value}.zip`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(downloadUrl)
    
    downloading.value = false
    downloadProgress.value = 100
    addLog('success', '文件下载完成')
    
    setTimeout(() => {
      downloadProgress.value = 0
    }, 2000)
    
  } catch (err) {
    downloading.value = false
    downloadError.value = err.message || '下载失败，请重试'
    addLog('error', '下载失败: ' + downloadError.value)
  }
}

function closeModal() {
  showCompleteModal.value = false
}

function resetAll() {
  if (progressTimer) { clearInterval(progressTimer); progressTimer = null }
  imageFile.value = null
  labelFiles.value = []
  authorAbbr.value = ''
  outputFormats.value = { tif: true, jpg_true: true, jpg_false: true }
  bandsTrue.value = '3,2,1'
  bandsFalse.value = '4,3,2'
  patchSize.value = '128x128'
  overlapRatio.value = '25%'
  status.value = 'idle'
  progress.value = 0
  displayProgress.value = 0
  progressMessage.value = ''
  logs.value = []
  taskId.value = ''
  lastLogMessage = ''
  showCompleteModal.value = false
  taskCompleted.value = false
  downloadInfo.value = null
  downloadError.value = null
  
  if (imageInput.value) {
    imageInput.value.value = ''
  }
  if (labelInput.value) {
    labelInput.value.value = ''
  }
  
  addLog('info', '遥感样本制作工具已就绪')
}

function parseStepProgress(msg) {
  const match = msg.match(/\[(\d+)\/(\d+)\]/)
  if (match) {
    const current = parseInt(match[1])
    const total = parseInt(match[2])
    if (!isNaN(current) && !isNaN(total) && total > 0) {
      return current / total
    }
  }
  return null
}

async function fetchLogs() {
  if (!taskId.value) return
  try {
    const res = await fetch(`/api/logs/${taskId.value}`)
    if (res.ok) {
      const data = await res.json()
      if (data.logs && data.logs.length > logs.value.length) {
        const seen = new Set()
        data.logs.slice(logs.value.length).forEach(msg => { 
          if (!seen.has(msg)) { 
            seen.add(msg)
            addLog('info', msg)
            
            if (status.value === 'processing' && !taskCompleted.value) {
              if (msg.includes('全部完成') || msg.includes('全部完成！') || msg.includes('处理完毕')) {
                progress.value = 100
                markTaskAsCompleted()
                return
              }
              
              const stepRatio = parseStepProgress(msg)
              if (stepRatio !== null) {
                const stepPercent = Math.floor(stepRatio * 100)
                if (stepPercent > progress.value && stepPercent < 100) {
                  progress.value = stepPercent
                  displayProgress.value = stepPercent
                }
              }
            }
          } 
        })
      }
    }
  } catch (e) { /* ignore */ }
}

function markTaskAsCompleted() {
  if (taskCompleted.value) return
  
  clearInterval(statusTimer)
  clearInterval(logTimer)
  status.value = 'completed'
  taskCompleted.value = true
  displayProgress.value = 100
  
  setTimeout(() => { 
    showCompleteModal.value = true 
  }, 300)
  
  fetchDownloadInfo()
}

async function stopProcess() {
  if (!taskId.value || status.value !== 'processing') return
  try {
    const res = await fetch(`/api/stop/${taskId.value}`, { method: 'POST' })
    if (res.ok) {
      addLog('warn', '任务已停止，正在清理生成的文件...')
    } else {
      addLog('error', '停止任务失败')
    }
  } catch (e) {
    addLog('error', '停止任务时发生错误: ' + e.message)
  }
  clearInterval(statusTimer)
  clearInterval(logTimer)
  if (progressTimer) { clearInterval(progressTimer); progressTimer = null }
  status.value = 'idle'
  progress.value = 0
  displayProgress.value = 0
}

async function checkRunningTasks() {
  try {
    const response = await fetch('/api/tasks')
    const tasks = await response.json()
    const processingTask = tasks.find(t => t.status === 'processing')
    const completedTask = tasks.find(t => t.status === 'completed')
    
    if (processingTask) {
      taskId.value = processingTask.task_id
      status.value = 'processing'
      addLog('info', `发现正在运行的任务: ${processingTask.task_id}`)
      startStatusPolling()
    } else if (completedTask) {
      taskId.value = completedTask.task_id
      status.value = 'completed'
      progress.value = 100
      displayProgress.value = 100
      addLog('info', `发现已完成的任务: ${completedTask.task_id}`)
      fetchDownloadInfo()
    }
  } catch (error) {
    addLog('error', '检查任务状态失败: ' + error.message)
  }
}

onMounted(() => { initTheme(); addLog('info', '遥感样本制作工具已就绪') })
onUnmounted(() => { clearInterval(statusTimer); clearInterval(logTimer); if (progressTimer) clearInterval(progressTimer) })
</script>

<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* ─── Dark Theme ─── */
[data-theme="dark"] {
  --bg:        #080C18;
  --surface:   #0D1424;
  --surface2:  #111928;
  --border:    #1A2840;
  --border-hi: #253460;
  --text-1:    #DDE6F0;
  --text-2:    #7A90B0;
  --text-3:    #3D5478;
  --blue:      #3B82F6;
  --blue-dim:  #1D4ED8;
  --blue-glow: rgba(59,130,246,0.20);
  --green:     #2ED882;
  --green-dim: rgba(46,216,130,0.12);
  --yellow:    #F0B040;
  --yellow-dim:rgba(240,176,64,0.10);
  --red:       #FF5565;
  --red-dim:   rgba(255,85,101,0.10);
  --log-bg:    #050A12;
  --log-border:#0D1828;
  --scroll:    #1C2D48;
  --shadow:    0 4px 20px rgba(0,0,0,0.6), 0 0 0 1px rgba(59,130,246,0.06);
  --shadow-hi: 0 8px 32px rgba(0,0,0,0.7), 0 0 0 1px var(--border-hi);
  --radius:    10px;
  --radius-sm: 6px;
  --btn-grad:  linear-gradient(135deg, #1D4ED8 0%, #3B82F6 100%);
  --btn-green: linear-gradient(135deg, #0EA86A 0%, #2ED882 100%);
}

/* ─── Light Theme ─── */
[data-theme="light"] {
  --bg:        #EEF2F8;
  --surface:   #FFFFFF;
  --surface2:  #F5F7FB;
  --border:    #D8E2F0;
  --border-hi: #B0C4F0;
  --text-1:    #1A2238;
  --text-2:    #566080;
  --text-3:    #9AAAC8;
  --blue:      #3B64E0;
  --blue-dim:  #1A3ABF;
  --blue-glow: rgba(59,100,224,0.10);
  --green:     #059669;
  --green-dim: rgba(5,150,105,0.08);
  --yellow:    #D97706;
  --yellow-dim:rgba(217,119,6,0.08);
  --red:       #DC2626;
  --red-dim:   rgba(220,38,38,0.08);
  --log-bg:    #EEF2F8;
  --log-border:#D8E2F0;
  --scroll:    #C5CEE0;
  --shadow:    0 2px 12px rgba(0,0,0,0.07);
  --shadow-hi: 0 4px 20px rgba(59,100,224,0.15);
  --radius:    10px;
  --radius-sm: 6px;
  --btn-grad:  linear-gradient(135deg, #3B64E0 0%, #5A82FF 100%);
  --btn-green: linear-gradient(135deg, #059669 0%, #34D399 100%);
}

html {
  background: #080C18;
  min-height: 100%;
}

body {
  font-family: 'Segoe UI', 'Microsoft YaHei', -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text-1);
  min-height: 100vh;
  transition: background .3s, color .3s;
  margin: 0;
  padding: 0;
}

.app-container { min-height: 100vh; display: flex; flex-direction: column; background: var(--bg); }

/* ─── Header ─── */
.app-header {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: .6rem 2rem;
  position: sticky; top: 0; z-index: 100;
  box-shadow: 0 1px 0 var(--border);
  transition: background .3s, border-color .3s, box-shadow .3s;
}
.header-content {
  max-width: 740px; margin: 0 auto;
  display: flex; justify-content: space-between; align-items: center;
}
.logo-section { display: flex; align-items: center; gap: .7rem; }
.logo-icon {
  width: 34px; height: 34px;
  background: var(--btn-grad);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center; color: #fff;
  flex-shrink: 0;
}
.logo-icon svg { width: 18px; height: 18px; }
.logo-text h1 { font-size: 1rem; font-weight: 700; color: var(--text-1); letter-spacing: .2px; }
.logo-text .subtitle { font-size: .65rem; color: var(--text-3); letter-spacing: .5px; text-transform: uppercase; }
.header-right { display: flex; align-items: center; gap: .6rem; }
.header-status {
  display: flex; align-items: center; gap: .3rem;
  padding: .28rem .7rem; border-radius: 20px;
  font-size: .72rem; font-weight: 600; letter-spacing: .3px;
  background: var(--green-dim); color: var(--green);
  transition: all .3s;
}
.header-status.processing { background: var(--yellow-dim); color: var(--yellow); }
.header-status.error { background: var(--red-dim); color: var(--red); }
.status-dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; animation: blink 2s ease-in-out infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }

.theme-btn {
  width: 32px; height: 32px;
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: var(--surface2); color: var(--text-2);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all .2s;
}
.theme-btn:hover { border-color: var(--blue); color: var(--blue); }

/* ─── Main ─── */
.main-content {
  flex: 1; max-width: 740px; width: 100%; margin: 0 auto;
  padding: 1.5rem 1.25rem 2rem;
  display: flex; flex-direction: column; gap: .85rem;
}
.config-section, .result-section { display: flex; flex-direction: column; gap: .85rem; }

/* ─── Panel ─── */
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  transition: border-color .25s, box-shadow .25s;
  overflow: hidden;
}
.panel:hover {
  border-color: var(--blue);
  box-shadow: 0 4px 20px rgba(0,0,0,0.5), 0 0 0 1px var(--blue), 0 0 16px rgba(59,130,246,0.15);
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: .75rem 1.1rem;
  border-bottom: 1px solid var(--border);
  background: var(--surface2);
}
.panel-title {
  display: flex; align-items: center; gap: .45rem;
  font-size: .78rem; font-weight: 700;
  color: var(--blue);
  letter-spacing: .5px;
  text-transform: uppercase;
}
.panel-title svg { color: var(--blue); flex-shrink: 0; }
.panel-body { padding: 1rem 1.1rem; }

/* ─── Fields ─── */
.field { display: flex; flex-direction: column; gap: .35rem; }
.field + .field { margin-top: .85rem; }
.field-label { font-size: .72rem; font-weight: 600; color: var(--text-2); letter-spacing: .3px; }
.field-hint { font-size: .68rem; color: var(--text-3); }
.field-row { display: flex; gap: .6rem; }
.field-row .field { flex: 1; }
.field-row .field + .field { margin-top: 0; }

.text-input {
  width: 100%; padding: .55rem .8rem;
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: var(--surface2); color: var(--text-1); font-size: .8rem;
  transition: border-color .25s, box-shadow .25s;
}
.text-input:hover { border-color: var(--blue); box-shadow: 0 0 0 3px var(--blue-glow); }
.text-input:focus { outline: none; border-color: var(--blue); box-shadow: 0 0 0 3px var(--blue-glow); }
.text-input::placeholder { color: var(--text-3); }
.text-input.small { max-width: 110px; }
.path-input { flex: 1; }

.select-input {
  width: 100%; padding: .55rem .8rem; padding-right: 2rem;
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: var(--surface2); color: var(--text-1); font-size: .8rem;
  cursor: pointer; transition: border-color .25s, box-shadow .25s;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 10 10'%3E%3Cpath fill='%233D5478' d='M5 7L0 2h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right .7rem center;
}
[data-theme="light"] .select-input { background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 10 10'%3E%3Cpath fill='%239AAAC8' d='M5 7L0 2h10z'/%3E%3C/svg%3E"); }
.select-input:hover { border-color: var(--blue); box-shadow: 0 0 0 3px var(--blue-glow); }
.select-input:focus { outline: none; border-color: var(--blue); box-shadow: 0 0 0 3px var(--blue-glow); }
.select-input option { background: var(--surface); color: var(--text-1); }

.path-row { display: flex; gap: .4rem; }
.icon-btn {
  padding: .55rem .65rem;
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: var(--surface2); color: var(--text-2);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all .2s; flex-shrink: 0;
}
.icon-btn:hover { border-color: var(--blue); color: var(--blue); }

/* ─── File Drop ─── */
.file-drop { position: relative; }
.file-input { position: absolute; opacity: 0; width: 0; height: 0; }
.file-drop-label {
  display: flex; align-items: center; justify-content: center; gap: .5rem;
  padding: .7rem 1rem;
  border: 1.5px dashed var(--border-hi); border-radius: var(--radius-sm);
  background: var(--surface2); color: var(--text-2);
  cursor: pointer; transition: all .2s; font-size: .78rem;
}
.file-drop:hover .file-drop-label, .file-drop.has-file .file-drop-label {
  border-color: var(--blue);
  background: var(--blue-glow);
  color: var(--blue);
}
.file-drop-label svg { flex-shrink: 0; }

.file-tags { display: flex; flex-wrap: wrap; gap: .3rem; margin-top: .3rem; }
.file-tag {
  padding: .15rem .55rem;
  background: var(--blue-glow); border: 1px solid rgba(77,124,255,0.2);
  border-radius: 20px; font-size: .68rem; color: var(--blue);
}

/* ─── Checkboxes ─── */
.checkbox-row { display: flex; gap: .5rem; flex-wrap: wrap; }
.check-chip {
  padding: .4rem .9rem;
  border: 1px solid var(--border); border-radius: 20px;
  cursor: pointer; transition: all .2s; font-size: .75rem; color: var(--text-2);
  background: var(--surface2);
}
.check-chip:hover { border-color: var(--blue); color: var(--blue); }
.check-chip.active { border-color: var(--blue); background: var(--blue-glow); color: var(--blue); font-weight: 600; }
.hidden-check { display: none; }

.divider { height: 1px; background: var(--border); margin: .85rem 0; }

/* ─── Action ─── */
.action-bar { margin-top: .15rem; }
.process-btn {
  width: 100%; padding: .85rem 1.5rem;
  display: flex; align-items: center; justify-content: center; gap: .6rem;
  background: var(--btn-grad); border: none; border-radius: var(--radius);
  color: #fff; font-size: .88rem; font-weight: 700; letter-spacing: .3px;
  cursor: pointer; transition: all .25s;
  box-shadow: 0 4px 16px rgba(38,83,255,0.3);
}
.process-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 28px rgba(38,83,255,0.4); }
.process-btn:disabled { opacity: .4; cursor: not-allowed; transform: none; }
.process-btn.processing { background: var(--yellow-dim); color: var(--yellow); box-shadow: none; }
.btn-icon { font-size: 1rem; }
.btn-spinner {
  width: 15px; height: 15px;
  border: 2px solid rgba(255,255,255,.25); border-top-color: #fff;
  border-radius: 50%; animation: spin .7s linear infinite;
}
.process-btn.processing .btn-spinner { border-color: rgba(240,176,64,.3); border-top-color: var(--yellow); }
@keyframes spin { to { transform: rotate(360deg); } }

/* ─── Status Panel ─── */
.status-panel .panel-header { border-bottom: none; padding-bottom: 0; background: transparent; }
.status-badge {
  font-size: .65rem; font-weight: 700; letter-spacing: .5px;
  padding: .18rem .6rem; border-radius: 20px;
  text-transform: uppercase;
  background: var(--green-dim); color: var(--green);
}
.status-badge.processing { background: var(--yellow-dim); color: var(--yellow); }
.status-badge.error { background: var(--red-dim); color: var(--red); }
.status-badge.idle { background: var(--surface2); color: var(--text-3); border: 1px solid var(--border); }

.progress-area { display: flex; align-items: center; gap: .9rem; margin-bottom: .6rem; }
.progress-track {
  flex: 1; height: 6px; min-width: 150px;
  background: var(--border); border-radius: 3px; overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: var(--btn-grad);
  border-radius: 3px;
  transition: width .5s ease-out;
  position: relative;
}
.progress-right { display: flex; align-items: center; gap: .7rem; min-width: 120px; }
.progress-pct { font-size: 1.25rem; font-weight: 800; color: var(--blue); min-width: 3rem; text-align: right; }
.progress-pct small { font-size: .7rem; font-weight: 500; }
.stop-btn {
  display: flex; align-items: center; gap: .35rem;
  padding: .35rem .7rem;
  border: 1px solid var(--red); border-radius: var(--radius-sm);
  background: var(--red-dim); color: var(--red);
  font-size: .72rem; font-weight: 600;
  cursor: pointer; transition: all .2s;
}
.stop-btn:hover {
  background: var(--red);
  color: #fff;
  box-shadow: 0 2px 12px rgba(255,85,101,0.3);
}

.status-message { font-size: .8rem; color: var(--text-2); }
.panel-idle { padding: 1.5rem 1.1rem; display: flex; flex-direction: column; align-items: center; gap: .6rem; text-align: center; }
.idle-icon { color: var(--text-3); }
.panel-idle p { font-size: .8rem; color: var(--text-3); }

/* ─── Log Panel ─── */
.log-terminal {
  background: var(--log-bg);
  border-top: 1px solid var(--log-border);
  height: 240px; overflow-y: auto;
  font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
  font-size: .72rem; line-height: 1.7;
}
.log-terminal::-webkit-scrollbar { width: 5px; }
.log-terminal::-webkit-scrollbar-track { background: transparent; }
.log-terminal::-webkit-scrollbar-thumb { background: var(--scroll); border-radius: 3px; }

.log-row {
  display: grid;
  grid-template-columns: 52px 55px 1fr;
  gap: .4rem;
  padding: .28rem .85rem;
  border-bottom: 1px solid var(--log-border);
  animation: fadeIn .2s ease;
}
@keyframes fadeIn { from{opacity:0} to{opacity:1} }
.log-row:last-child { border-bottom: none; }
.log-ts { color: var(--text-3); flex-shrink: 0; }
.log-type { color: var(--text-3); flex-shrink: 0; }
.log-msg { color: var(--text-2); word-break: break-all; }
.log-row.info  .log-msg { color: var(--text-1); }
.log-row.success .log-msg { color: var(--green); }
.log-row.error .log-msg { color: var(--red); }
.log-row.warn  .log-msg { color: var(--yellow); }
.log-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 100%; gap: .4rem; color: var(--text-3);
}
.log-empty span { font-size: 1.5rem; }
.log-empty p { font-size: .72rem; }

.ghost-btn {
  padding: .2rem .55rem;
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: transparent; color: var(--text-3); font-size: .65rem; cursor: pointer;
  transition: all .2s; letter-spacing: .3px;
}
.ghost-btn:hover { border-color: var(--red); color: var(--red); background: var(--red-dim); }

/* ─── Download ─── */
.download-panel {
  display: flex; flex-direction: column; align-items: center; gap: .5rem;
  padding: 1.5rem !important; text-align: center;
}
.success-icon {
  width: 52px; height: 52px;
  background: var(--green-dim); border: 1px solid rgba(46,216,130,0.25);
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  color: var(--green); margin-bottom: .25rem;
}
.success-title { font-size: 1rem; font-weight: 700; color: var(--green); }
.success-desc { font-size: .78rem; color: var(--text-3); }
.download-btn {
  display: inline-flex; align-items: center; gap: .45rem;
  padding: .7rem 1.8rem;
  background: var(--btn-green); border-radius: var(--radius);
  color: #fff; text-decoration: none; font-size: .85rem; font-weight: 700;
  transition: all .25s; margin-top: .35rem;
  box-shadow: 0 4px 16px rgba(14,168,106,0.3);
}
.download-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 28px rgba(14,168,106,0.4); }
.download-btn:disabled { 
  opacity: 1; 
  cursor: not-allowed; 
  background: var(--surface2); 
  color: var(--text-3); 
  box-shadow: none;
}

.success-icon.disabled {
  color: var(--text-4);
}
.success-title:has(+ .success-icon.disabled),
.success-title + .success-desc:has(+ .download-info) {
  color: var(--text-3);
}

.download-info {
  width: 100%;
  padding: .75rem 1rem;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  margin-bottom: .5rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: .35rem 0;
  border-bottom: 1px solid var(--border);
}

.info-item:last-child { border-bottom: none; }

.info-label {
  font-size: .72rem;
  color: var(--text-3);
  font-weight: 500;
}

.info-value {
  font-size: .78rem;
  color: var(--text-1);
  font-weight: 600;
}

.download-progress {
  width: 100%;
  margin-bottom: .5rem;
}

.download-progress .progress-track {
  height: 8px;
  background: var(--border);
  border-radius: 4px;
  overflow: hidden;
}

.download-progress .progress-fill {
  background: var(--btn-green);
  border-radius: 4px;
  transition: width .3s ease;
}

.download-progress .progress-text {
  display: block;
  text-align: center;
  font-size: .75rem;
  color: var(--text-2);
  margin-top: .25rem;
}

.download-error {
  display: flex;
  align-items: center;
  gap: .5rem;
  padding: .6rem 1rem;
  background: rgba(255,85,101,0.1);
  border: 1px solid rgba(255,85,101,0.3);
  border-radius: var(--radius-sm);
  margin-bottom: .5rem;
  font-size: .78rem;
  color: var(--red);
}

.retry-btn {
  padding: .35rem .85rem;
  background: var(--btn-blue);
  border: none;
  border-radius: var(--radius-sm);
  color: #fff;
  font-size: .72rem;
  font-weight: 600;
  cursor: pointer;
  transition: all .2s;
}

.retry-btn:hover {
  background: var(--btn-blue-hover);
  transform: translateY(-1px);
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ─── Footer ─── */
.app-footer {
  text-align: center; padding: .8rem;
  color: var(--text-3); font-size: .7rem;
  border-top: 1px solid var(--border);
  background: var(--surface);
  transition: all .3s;
}

/* ─── Modal ─── */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn .2s ease;
}

.modal-content {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.75rem 2rem;
  min-width: 340px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  animation: slideUp .3s ease;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.modal-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto .8rem;
  background: var(--green-dim);
  border: 2px solid rgba(46, 216, 130, 0.3);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--green);
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-1);
  margin-bottom: .4rem;
}

.modal-desc {
  font-size: .85rem;
  color: var(--text-2);
  margin-bottom: 1.25rem;
}

.modal-actions {
  display: flex;
  gap: .65rem;
  justify-content: center;
}

.modal-btn {
  padding: .65rem 1.4rem;
  border-radius: var(--radius-sm);
  font-size: .85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all .25s;
  border: none;
}

.modal-btn-secondary {
  background: var(--surface2);
  color: var(--text-2);
  border: 1px solid var(--border);
}

.modal-btn-secondary:hover {
  background: var(--border);
  color: var(--text-1);
}

.modal-btn-primary {
  background: var(--btn-grad);
  color: #fff;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.modal-btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

/* ─── Responsive ─── */
@media (max-width: 599px) {
  .main-content { padding: 1rem; gap: .75rem; }
  .app-header { padding: .5rem 1rem; }
  .header-content { flex-direction: column; gap: .4rem; }
  .logo-text h1 { font-size: .95rem; }
  .field-row { flex-direction: column; }
  .text-input.small { max-width: 100%; }
  .checkbox-row { gap: .35rem; }
  .modal-content { min-width: 280px; padding: 1.5rem 1.5rem; }
}
</style>
