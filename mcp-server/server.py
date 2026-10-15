"""
学生管理系统 MCP Server
=====================
通过 MCP（Model Context Protocol）协议，把云端 FastAPI 后端的能力
包装成标准工具，供 WorkBuddy 等 MCP 客户端调用。

概念说明：
- MCP（Model Context Protocol）：一种开放协议，让 AI 应用能通过统一的
  方式发现并调用外部工具/数据源。本文件就是一个「MCP Server」。
- 每个 @mcp.tool 装饰的函数，就是一个「工具（Tool）」，会被注册到 MCP 客户端。
- 工具内部通过 HTTP 调用云端 REST API（GET/POST/PUT/DELETE）。
"""

import os

import httpx
from mcp.server.fastmcp import FastMCP

# 云端学生管理系统后端地址（可通过环境变量覆盖）
API_BASE = os.getenv("STUDENT_API_BASE", "http://47.110.229.114/api")

mcp = FastMCP("student-system")


async def _request(method: str, path: str, **kwargs) -> dict:
    """统一的 HTTP 请求封装，调用云端 REST API。"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.request(method, f"{API_BASE}{path}", **kwargs)
        resp.raise_for_status()
        if resp.status_code == 204:
            return {"ok": True}
        return resp.json()


@mcp.tool()
async def list_students(q: str = "", class_name: str = "", sort_by: str = "name",
                        order: str = "asc") -> list:
    """查询学生列表。支持按姓名/学号/班级模糊搜索(q)、按班级筛选(class_name)、
    按字段排序(sort_by: name/className/age/score, order: asc/desc)。"""
    params = {"q": q, "className": class_name, "sortBy": sort_by, "order": order}
    return await _request("GET", "/students", params=params)


@mcp.tool()
async def add_student(id: str, name: str, class_name: str,
                      age: int = 0, score: float = 0) -> dict:
    """新增一名学生。id=学号(唯一), name=姓名, class_name=班级,
    age=年龄, score=成绩(0-100)。"""
    payload = {"id": id, "name": name, "className": class_name,
               "age": age, "score": score}
    return await _request("POST", "/students", json=payload)


@mcp.tool()
async def update_student(id: str, name: str, class_name: str,
                         age: int = 0, score: float = 0) -> dict:
    """修改指定学号(id)的学生信息。"""
    payload = {"name": name, "className": class_name, "age": age, "score": score}
    return await _request("PUT", f"/students/{id}", json=payload)


@mcp.tool()
async def delete_student(id: str) -> dict:
    """删除指定学号(id)的学生。"""
    return await _request("DELETE", f"/students/{id}")


@mcp.tool()
async def get_stats() -> dict:
    """获取统计信息：学生总数、班级数、平均成绩、优秀人数(≥90分)。"""
    return await _request("GET", "/stats")


@mcp.tool()
async def list_classes() -> list:
    """获取所有班级名称列表。"""
    data = await _request("GET", "/classes")
    return data.get("classes", [])


if __name__ == "__main__":
    # 以 stdio 方式运行，供 MCP 客户端（如 WorkBuddy）拉起
    mcp.run()
