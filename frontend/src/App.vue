<template>
  <nav class="nav">
    <div class="nav-inner">
      <div class="nav-logo"><span class="dot">🎓</span>EduManager</div>
      <div class="nav-sub">
        API 数据源：
        <select v-model="activeSource" class="source-select" @change="switchSource(activeSource)">
          <option v-for="s in sources" :key="s.key" :value="s.key">{{ s.name }}</option>
        </select>
      </div>
    </div>
  </nav>

  <div class="container">
    <div class="hero">
      <h1>学生管理，化繁为简。</h1>
      <p>录入、查询、编辑、统计，一切尽在掌握。</p>
    </div>

    <div class="stats">
      <div class="stat-card"><div class="icon icon-blue">🎓</div><div class="value">{{ stats.total }}</div><div class="label">学生总数</div></div>
      <div class="stat-card"><div class="icon icon-purple">🏫</div><div class="value">{{ stats.class_count }}</div><div class="label">班级数量</div></div>
      <div class="stat-card"><div class="icon icon-orange">📊</div><div class="value">{{ stats.avg_score ?? '—' }}</div><div class="label">平均成绩</div></div>
      <div class="stat-card"><div class="icon icon-green">🌟</div><div class="value">{{ stats.excellent }}</div><div class="label">优秀学生（≥90 分）</div></div>
    </div>

    <div class="toolbar">
      <div class="search-box">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">
          <circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>
        </svg>
        <input v-model="query" type="text" placeholder="搜索姓名、学号或班级…" @input="debouncedLoad">
      </div>
      <div class="select-wrap">
        <select v-model="classFilter" @change="loadStudents">
          <option value="">全部班级</option>
          <option v-for="c in classes" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>
      <button class="btn btn-ghost" @click="exportCSV">⬇︎ 导出 CSV</button>
      <button class="btn btn-primary" @click="openModal()">＋ 添加学生</button>
    </div>

    <div class="panel">
      <div class="panel-header">
        <h2>学生列表</h2>
        <span>共 {{ students.length }} 人</span>
      </div>
      <div style="overflow-x:auto">
        <table>
          <thead>
            <tr>
              <th @click="toggleSort('name')">学生<span class="arrow">{{ arrow('name') }}</span></th>
              <th class="hide-mobile" @click="toggleSort('className')">班级<span class="arrow">{{ arrow('className') }}</span></th>
              <th class="hide-mobile" @click="toggleSort('age')">年龄<span class="arrow">{{ arrow('age') }}</span></th>
              <th @click="toggleSort('score')">成绩<span class="arrow">{{ arrow('score') }}</span></th>
              <th style="cursor:default">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in students" :key="s.id">
              <td>
                <div class="student-cell">
                  <div class="avatar" :style="{ background: avatarColor(s.id) }">{{ s.name.slice(0, 1) }}</div>
                  <div>
                    <div class="student-name">{{ s.name }}</div>
                    <div class="student-id">{{ s.id }}</div>
                  </div>
                </div>
              </td>
              <td class="hide-mobile"><span class="tag">{{ s.className }}</span></td>
              <td class="hide-mobile">{{ s.age }} 岁</td>
              <td><span class="score-pill" :class="scoreClass(s.score)">{{ s.score }}</span></td>
              <td style="white-space:nowrap">
                <button class="btn btn-link" @click="openModal(s)">编辑</button>
                <button class="btn btn-danger-text" @click="removeStudent(s)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="empty" v-if="!loading && students.length === 0">
        <span class="emoji">📭</span>
        没有找到匹配的学生，试试调整搜索条件<br>或点击「添加学生」录入新成员。
      </div>
      <div class="empty" v-if="loading">
        <span class="emoji">⏳</span>正在加载…
      </div>
    </div>
  </div>

  <footer>Designed with ♥ in Apple Style · FastAPI + Vue3 + MySQL</footer>

  <!-- 添加/编辑弹窗 -->
  <div class="modal-mask" :class="{ show: modalVisible }" @click.self="closeModal">
    <div class="modal">
      <h3>{{ editingId ? '编辑学生' : '添加学生' }}</h3>
      <div class="field">
        <label>姓名 *</label>
        <input v-model.trim="form.name" type="text" placeholder="例如：陈晓" maxlength="20" ref="nameInput">
      </div>
      <div class="field">
        <label>学号 *</label>
        <input v-model.trim="form.id" type="text" placeholder="例如：20260101" maxlength="20" :disabled="!!editingId">
      </div>
      <div class="field">
        <label>班级 / 专业 *</label>
        <input v-model.trim="form.className" type="text" placeholder="例如：软件工程" maxlength="30" list="classList">
        <datalist id="classList">
          <option v-for="c in classes" :key="c" :value="c"></option>
        </datalist>
      </div>
      <div class="field">
        <label>年龄</label>
        <input v-model.number="form.age" type="number" placeholder="6 – 60" min="6" max="60">
      </div>
      <div class="field">
        <label>成绩（0 – 100）</label>
        <input v-model.number="form.score" type="number" placeholder="0 – 100" min="0" max="100">
      </div>
      <div class="modal-actions">
        <button class="btn btn-ghost" @click="closeModal">取消</button>
        <button class="btn btn-primary" :disabled="saving" @click="saveStudent">{{ saving ? '保存中…' : '保存' }}</button>
      </div>
    </div>
  </div>

  <div class="toast" :class="{ show: toastVisible }">{{ toastMsg }}</div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import {
  fetchStudents, createStudent, updateStudent, deleteStudent,
  fetchClasses, fetchStats, setSource, sourceList
} from './api/index.js'

const sources = sourceList()
const activeSource = ref('classmate')
const currentSourceName = ref(sources.find(s => s.key === 'classmate').name)

const AVATAR_COLORS = ['#0071e3', '#34c759', '#ff9500', '#af52de', '#ff3b30', '#5ac8fa', '#ff6482', '#30d158']

const students = ref([])
const classes = ref([])
const stats = reactive({ total: 0, class_count: 0, avg_score: null, excellent: 0 })
const query = ref('')
const classFilter = ref('')
const sortBy = ref('name')
const order = ref('asc')
const loading = ref(false)

const modalVisible = ref(false)
const editingId = ref(null)      // 编辑时记录的数据库主键 dbId
const saving = ref(false)
const nameInput = ref(null)
const emptyForm = () => ({ name: '', id: '', className: '', age: null, score: null })
const form = reactive(emptyForm())

const toastMsg = ref('')
const toastVisible = ref(false)
let toastTimer = null

function toast(msg) {
  toastMsg.value = msg
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 2200)
}

async function loadStudents() {
  loading.value = true
  try {
    students.value = await fetchStudents({
      q: query.value, className: classFilter.value,
      sortBy: sortBy.value, order: order.value
    })
  } catch (e) {
    toast(e.message)
  } finally {
    loading.value = false
  }
}

async function loadMeta() {
  try {
    const [cls, st] = await Promise.all([fetchClasses(), fetchStats()])
    classes.value = cls.classes
    Object.assign(stats, st)
  } catch (e) {
    toast(e.message)
  }
}

async function refreshAll() {
  await Promise.all([loadStudents(), loadMeta()])
}

// 切换数据源（本系统 / 同学后端）
async function switchSource(key) {
  setSource(key)
  activeSource.value = key
  currentSourceName.value = sources.find(s => s.key === key).name
  classFilter.value = ''          // 重置筛选条件
  query.value = ''
  await refreshAll()
  toast(`已切换到：${currentSourceName.value}`)
}

let debounceTimer = null
function debouncedLoad() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadStudents, 300)
}

function toggleSort(key) {
  if (sortBy.value === key) order.value = order.value === 'asc' ? 'desc' : 'asc'
  else { sortBy.value = key; order.value = 'asc' }
  loadStudents()
}

function arrow(key) {
  return sortBy.value === key ? (order.value === 'asc' ? '▲' : '▼') : ''
}

function avatarColor(id) {
  let h = 0
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0
  return AVATAR_COLORS[h % AVATAR_COLORS.length]
}

function scoreClass(score) {
  return score >= 80 ? 'score-high' : score >= 60 ? 'score-mid' : 'score-low'
}

function openModal(student) {
  editingId.value = student ? student.dbId : null
  Object.assign(form, student ? {
    name: student.name, id: student.id,
    className: student.className, age: student.age, score: student.score
  } : emptyForm())
  modalVisible.value = true
  setTimeout(() => nameInput.value?.focus(), 250)
}

function closeModal() {
  modalVisible.value = false
}

async function saveStudent() {
  if (!form.name || !form.id || !form.className) return toast('请填写姓名、学号和班级')
  if (form.age != null && form.age !== '' && (form.age < 6 || form.age > 60)) return toast('年龄需在 6 – 60 之间')
  if (form.score == null || form.score === '' || form.score < 0 || form.score > 100) return toast('成绩需在 0 – 100 之间')

  saving.value = true
  try {
    const payload = {
      name: form.name, className: form.className,
      age: form.age || 0, score: form.score
    }
    if (editingId.value) {
      await updateStudent(editingId.value, payload)
      toast('已保存修改 ✓')
    } else {
      await createStudent({ id: form.id, ...payload })
      toast('添加成功 ✓')
    }
    closeModal()
    await refreshAll()
  } catch (e) {
    toast(e.message)
  } finally {
    saving.value = false
  }
}

async function removeStudent(s) {
  if (!confirm(`确定删除「${s.name}」（${s.id}）吗？`)) return
  try {
    await deleteStudent(s.dbId)
    toast('已删除')
    await refreshAll()
  } catch (e) {
    toast(e.message)
  }
}

function exportCSV() {
  const rows = [['姓名', '学号', '班级', '年龄', '成绩'],
    ...students.value.map(s => [s.name, s.id, s.className, s.age, s.score])]
  const csv = '﻿' + rows.map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  a.download = `学生名单_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(a.href)
  toast('已导出 CSV ✓')
}

onMounted(() => {
  refreshAll()
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal() })
})
</script>

<style>
:root {
  --bg: #f5f5f7;
  --card: #ffffff;
  --text: #1d1d1f;
  --text-secondary: #86868b;
  --accent: #0071e3;
  --accent-hover: #0077ed;
  --red: #ff3b30;
  --border: rgba(0, 0, 0, 0.08);
  --shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  --shadow-hover: 0 8px 32px rgba(0, 0, 0, 0.1);
  --radius: 18px;
}

* { margin: 0; padding: 0; box-sizing: border-box; -webkit-font-smoothing: antialiased; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}

.nav {
  position: sticky; top: 0; z-index: 100;
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  background: rgba(251, 251, 253, 0.72);
  border-bottom: 1px solid var(--border);
}
.nav-inner { max-width: 1100px; margin: 0 auto; padding: 14px 24px; display: flex; align-items: center; justify-content: space-between; }
.nav-logo { font-size: 17px; font-weight: 600; letter-spacing: -0.02em; display: flex; align-items: center; gap: 8px; }
.nav-logo .dot {
  width: 26px; height: 26px; border-radius: 8px;
  background: linear-gradient(135deg, #0071e3, #42a5f5);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 14px;
}
.nav-sub { font-size: 13px; color: var(--text-secondary); display: flex; align-items: center; gap: 6px; }
.source-select {
  font-size: 13px; color: var(--text);
  border: 1px solid var(--border); border-radius: 980px;
  background: var(--card); padding: 5px 12px; cursor: pointer;
  font-family: inherit; outline: none;
}
.source-select:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(0,113,227,0.12); }

.container { max-width: 1100px; margin: 0 auto; padding: 32px 24px 80px; }

.hero { text-align: center; padding: 28px 0 36px; }
.hero h1 {
  font-size: clamp(32px, 5vw, 48px); font-weight: 700; letter-spacing: -0.03em;
  background: linear-gradient(135deg, #1d1d1f 30%, #0071e3);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent;
}
.hero p { margin-top: 10px; font-size: 17px; color: var(--text-secondary); }

.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 28px; }
.stat-card { background: var(--card); border-radius: var(--radius); padding: 22px; box-shadow: var(--shadow); transition: transform 0.25s ease, box-shadow 0.25s ease; }
.stat-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-hover); }
.stat-card .icon { width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; margin-bottom: 14px; }
.stat-card .value { font-size: 30px; font-weight: 700; letter-spacing: -0.02em; }
.stat-card .label { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }
.icon-blue { background: rgba(0,113,227,0.12); }
.icon-green { background: rgba(52,199,89,0.14); }
.icon-orange { background: rgba(255,149,0,0.14); }
.icon-purple { background: rgba(175,82,222,0.13); }

.toolbar { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; margin-bottom: 20px; }
.search-box {
  flex: 1; min-width: 220px; display: flex; align-items: center; gap: 8px;
  background: var(--card); border: 1px solid var(--border);
  border-radius: 980px; padding: 10px 18px; transition: box-shadow 0.2s;
}
.search-box:focus-within { box-shadow: 0 0 0 4px rgba(0,113,227,0.15); border-color: var(--accent); }
.search-box input { border: none; outline: none; background: transparent; font-size: 15px; width: 100%; color: var(--text); font-family: inherit; }
.search-box svg { flex-shrink: 0; opacity: 0.4; }

.select-wrap { background: var(--card); border: 1px solid var(--border); border-radius: 980px; padding: 10px 16px; }
.select-wrap select { border: none; outline: none; background: transparent; font-size: 14px; color: var(--text); font-family: inherit; cursor: pointer; }

.btn {
  border: none; border-radius: 980px; padding: 11px 22px;
  font-size: 15px; font-weight: 500; cursor: pointer; font-family: inherit;
  transition: transform 0.15s, background 0.2s, box-shadow 0.2s;
  display: inline-flex; align-items: center; gap: 6px;
}
.btn:active { transform: scale(0.96); }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:hover { background: var(--accent-hover); box-shadow: 0 4px 16px rgba(0,113,227,0.35); }
.btn-ghost { background: var(--card); color: var(--accent); border: 1px solid var(--border); }
.btn-ghost:hover { background: rgba(0,113,227,0.06); }
.btn-danger-text { background: transparent; color: var(--red); padding: 6px 12px; font-size: 13px; }
.btn-danger-text:hover { background: rgba(255,59,48,0.08); }
.btn-link { background: transparent; color: var(--accent); padding: 6px 12px; font-size: 13px; }
.btn-link:hover { background: rgba(0,113,227,0.08); }

.panel { background: var(--card); border-radius: var(--radius); box-shadow: var(--shadow); overflow: hidden; }
.panel-header { padding: 18px 24px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
.panel-header h2 { font-size: 17px; font-weight: 600; }
.panel-header span { font-size: 13px; color: var(--text-secondary); }

table { width: 100%; border-collapse: collapse; }
thead th {
  text-align: left; font-size: 12px; font-weight: 600; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 0.04em;
  padding: 12px 24px; border-bottom: 1px solid var(--border);
  cursor: pointer; user-select: none; white-space: nowrap;
}
thead th:hover { color: var(--accent); }
thead th .arrow { font-size: 10px; margin-left: 4px; }
tbody td { padding: 14px 24px; font-size: 15px; border-bottom: 1px solid var(--border); vertical-align: middle; }
tbody tr:last-child td { border-bottom: none; }
tbody tr { transition: background 0.15s; }
tbody tr:hover { background: rgba(0,0,0,0.02); }

.student-cell { display: flex; align-items: center; gap: 12px; }
.avatar { width: 38px; height: 38px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 14px; font-weight: 600; flex-shrink: 0; }
.student-name { font-weight: 500; }
.student-id { font-size: 12px; color: var(--text-secondary); }

.tag { display: inline-block; padding: 4px 12px; border-radius: 980px; font-size: 12px; font-weight: 500; background: rgba(0,113,227,0.1); color: var(--accent); }
.score-pill { display: inline-block; min-width: 44px; text-align: center; padding: 4px 10px; border-radius: 980px; font-size: 13px; font-weight: 600; }
.score-high { background: rgba(52,199,89,0.14); color: #248a3d; }
.score-mid { background: rgba(255,149,0,0.14); color: #c93400; }
.score-low { background: rgba(255,59,48,0.12); color: var(--red); }

.empty { text-align: center; padding: 64px 24px; color: var(--text-secondary); }
.empty .emoji { font-size: 44px; display: block; margin-bottom: 12px; }

.modal-mask {
  position: fixed; inset: 0; z-index: 200;
  background: rgba(0,0,0,0.35);
  backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center;
  opacity: 0; pointer-events: none; transition: opacity 0.25s; padding: 20px;
}
.modal-mask.show { opacity: 1; pointer-events: auto; }
.modal {
  background: var(--card); border-radius: 22px; width: 100%; max-width: 440px;
  padding: 28px; transform: scale(0.92) translateY(12px);
  transition: transform 0.25s cubic-bezier(0.34, 1.3, 0.64, 1);
  max-height: 90vh; overflow-y: auto;
}
.modal-mask.show .modal { transform: scale(1) translateY(0); }
.modal h3 { font-size: 20px; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 20px; }
.field { margin-bottom: 16px; }
.field label { display: block; font-size: 13px; font-weight: 500; color: var(--text-secondary); margin-bottom: 6px; }
.field input {
  width: 100%; padding: 12px 14px; font-size: 15px; font-family: inherit;
  color: var(--text); background: var(--bg);
  border: 1px solid transparent; border-radius: 12px; outline: none;
  transition: border 0.2s, box-shadow 0.2s;
}
.field input:focus { background: var(--card); border-color: var(--accent); box-shadow: 0 0 0 4px rgba(0,113,227,0.12); }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 24px; }

.toast {
  position: fixed; bottom: 32px; left: 50%; z-index: 300;
  transform: translateX(-50%) translateY(80px);
  background: rgba(29,29,31,0.92); color: #fff;
  padding: 12px 24px; border-radius: 980px; font-size: 14px;
  transition: transform 0.35s cubic-bezier(0.34, 1.3, 0.64, 1);
  backdrop-filter: blur(10px);
}
.toast.show { transform: translateX(-50%) translateY(0); }

footer { text-align: center; padding: 24px; font-size: 12px; color: var(--text-secondary); }

@media (max-width: 720px) {
  .hide-mobile { display: none; }
  tbody td, thead th { padding: 12px 14px; }
  .panel-header { padding: 16px; }
}
</style>
