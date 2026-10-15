// ============================================================
// 本系统后端的 API 实现（数据源：own）
// ============================================================
// 对应自己部署的 FastAPI 后端，接口约定：
//   - 返回裸数组 / 对象，字段为 id/name/className/age/score
//   - 用学号(id)作为增删改的路径参数

import { SOURCES } from './config.js'

const BASE = SOURCES.own.baseURL

async function request(method, path, body) {
  const res = await fetch(BASE + path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined
  })
  if (!res.ok) {
    let detail = `请求失败(${res.status})`
    try { const d = await res.json(); if (d.detail) detail = d.detail } catch {}
    throw new Error(detail)
  }
  if (res.status === 204) return null
  return res.json()
}

export async function fetchStudents({ q = '', className = '', sortBy = 'name', order = 'asc' } = {}) {
  const p = new URLSearchParams({ q, className, sortBy, order })
  return request('GET', `/students?${p}`)
}

export async function createStudent(s) {
  return request('POST', '/students', { id: s.id, name: s.name, className: s.className, age: s.age || 0, score: s.score || 0 })
}

export async function updateStudent(dbId, s) {
  return request('PUT', `/students/${encodeURIComponent(dbId)}`, { name: s.name, className: s.className, age: s.age || 0, score: s.score || 0 })
}

export async function deleteStudent(dbId) {
  return request('DELETE', `/students/${encodeURIComponent(dbId)}`)
}

export async function fetchClasses() {
  return request('GET', '/classes')
}

export async function fetchStats() {
  return request('GET', '/stats')
}
