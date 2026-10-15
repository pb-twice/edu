// ============================================================
// API 层统一入口 —— 前端只 import 这里，不感知具体后端
// ============================================================
// 支持「动态切换数据源」：通过 setSource() 在运行时切换，
// 所有 API 函数都会路由到当前选中的后端实现。
// 这是「依赖注入 / 适配器模式」：上层只依赖统一接口，具体连谁由状态决定。

import { SOURCES } from './config.js'
import * as own from './own.js'
import * as classmate from './classmate.js'

const impls = { own, classmate }

let active = 'classmate'   // 默认数据源

// 运行时切换数据源
export function setSource(key) {
  if (!impls[key]) throw new Error(`未知数据源: ${key}`)
  active = key
}

export function currentSource() {
  return active
}

export function sourceList() {
  return Object.entries(SOURCES).map(([key, v]) => ({ key, name: v.name }))
}

function impl() {
  return impls[active]
}

export const fetchStudents = (...a) => impl().fetchStudents(...a)
export const createStudent = (...a) => impl().createStudent(...a)
export const updateStudent = (...a) => impl().updateStudent(...a)
export const deleteStudent = (...a) => impl().deleteStudent(...a)
export const fetchClasses = (...a) => impl().fetchClasses(...a)
export const fetchStats = (...a) => impl().fetchStats(...a)
