// ============================================================
// 同学后端的 API 实现（数据源：classmate）
// ============================================================
// 对应同学部署的后端（114.55.8.171），接口约定与自己的后端不同：
//   - 返回 {"code":0,"data":...} 包裹结构
//   - 字段为 student_id/name/major/gender/age/score
//   - 增删改用数据库主键(id)作为路径参数
// 本模块负责「数据契约适配」，把同学的数据翻译成前端统一的格式。

import { SOURCES } from './config.js'

const BASE = SOURCES.classmate.baseURL

async function request(method, path, body) {
  const res = await fetch(BASE + path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined
  })
  const json = await res.json()
  if (json.code !== 0) throw new Error(json.msg || `请求失败(${json.code})`)
  return json.data
}

function toStudent(s) {
  return {
    id: String(s.student_id),   // 学号
    dbId: s.id,                  // 数据库主键（增删改路径参数）
    name: s.name,
    className: s.major,          // 同学的 major → 前端 className
    age: s.age,
    score: s.score,
    gender: s.gender
  }
}

export async function fetchStudents({ q = '', className = '', sortBy = 'name', order = 'asc' } = {}) {
  const data = await request('GET', '/students')
  let list = (data || []).map(toStudent)
  if (q) {
    const k = q.toLowerCase()
    list = list.filter(s => s.name.toLowerCase().includes(k) || s.id.toLowerCase().includes(k) || s.className.toLowerCase().includes(k))
  }
  if (className) list = list.filter(s => s.className === className)
  list.sort((a, b) => {
    let va = a[sortBy], vb = b[sortBy]
    if (typeof va === 'string') { const c = va.localeCompare(vb, 'zh'); return order === 'asc' ? c : -c }
    return order === 'asc' ? va - vb : vb - va
  })
  return list
}

export async function createStudent(s) {
  await request('POST', '/students', {
    student_id: s.id, name: s.name, major: s.className,
    age: s.age || 0, score: s.score || 0, gender: s.gender || '男'
  })
}

export async function updateStudent(dbId, s) {
  await request('PUT', `/students/${dbId}`, {
    name: s.name, major: s.className, age: s.age || 0,
    score: s.score || 0, gender: s.gender || '男'
  })
}

export async function deleteStudent(dbId) {
  await request('DELETE', `/students/${dbId}`)
}

export async function fetchClasses() {
  const data = await request('GET', '/students')
  return { classes: [...new Set((data || []).map(s => s.major))].sort() }
}

export async function fetchStats() {
  const d = await request('GET', '/stats')
  const students = await request('GET', '/students')
  return {
    total: d.total,
    class_count: new Set((students || []).map(s => s.major)).size,
    avg_score: d.avg_score,
    excellent: (students || []).filter(s => s.score >= 90).length
  }
}
