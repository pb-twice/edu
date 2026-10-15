const BASE = '/api'

async function request(url, options = {}) {
  const res = await fetch(BASE + url, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  })
  if (!res.ok) {
    let detail = `请求失败（${res.status}）`
    try {
      const data = await res.json()
      if (data.detail) detail = typeof data.detail === 'string' ? data.detail : detail
    } catch { /* ignore */ }
    throw new Error(detail)
  }
  if (res.status === 204) return null
  return res.json()
}

export function fetchStudents({ q = '', className = '', sortBy = 'name', order = 'asc' } = {}) {
  const params = new URLSearchParams({ q, className, sortBy, order })
  return request(`/students?${params}`)
}

export function createStudent(student) {
  return request('/students', { method: 'POST', body: JSON.stringify(student) })
}

export function updateStudent(id, student) {
  return request(`/students/${encodeURIComponent(id)}`, { method: 'PUT', body: JSON.stringify(student) })
}

export function deleteStudent(id) {
  return request(`/students/${encodeURIComponent(id)}`, { method: 'DELETE' })
}

export function fetchClasses() {
  return request('/classes')
}

export function fetchStats() {
  return request('/stats')
}
