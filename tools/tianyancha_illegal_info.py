from collections.abc import Generator
from typing import Any
import requests
from datetime import datetime

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

class TianyanchaIllegalInfoTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        获取企业严重违法信息
        
        参数:
            tool_parameters: 包含查询参数的字典
                - company_keyword: 公司关键词(名称或ID)
                - page_size: 每页数据量，默认20
                - page_num: 页码，默认1
        """
        # 获取参数
        company_keyword = tool_parameters.get("company_keyword")
        page_size = tool_parameters.get("page_size", 20)
        page_num = tool_parameters.get("page_num", 1)
        
        if not company_keyword:
            error_message = "公司关键词不能为空"
            yield self.create_json_message({"error": error_message})
            return
            
        # 从runtime获取凭证
        try:
            token = self.runtime.credentials["token"]
        except (KeyError, AttributeError):
            error_message = "API token未配置，请在插件设置中提供有效的天眼查API Token"
            yield self.create_json_message({"error": error_message})
            return
        
        # 调用API获取严重违法信息
        try:
            result = self._get_company_illegal_info(company_keyword, token, page_size, page_num)
            
            # 返回结构化JSON数据
            yield self.create_json_message(result)
        except Exception as e:
            error_message = f"请求过程中发生错误: {str(e)}"
            yield self.create_json_message({"error": error_message})
            
    def _format_timestamp(self, timestamp):
        """格式化时间戳为可读日期"""
        if not timestamp:
            return None
        try:
            # 毫秒时间戳转为秒
            if len(str(timestamp)) > 10:
                timestamp = int(timestamp) / 1000
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            return None
    
    def _get_company_illegal_info(self, company_keyword: str, token: str, page_size: int = 20, page_num: int = 1) -> dict:
        """
        获取企业严重违法信息的API调用实现
        
        参数:
            company_keyword: 公司关键词
            token: API凭证
            page_size: 每页数据量
            page_num: 页码
            
        返回:
            格式化后的企业严重违法信息
        """
        # 构建请求
        url = f"http://open.api.tianyancha.com/services/open/mr/illegalinfo/2.0?keyword={company_keyword}&pageSize={page_size}&pageNum={page_num}"
        headers = {'Authorization': token}
        
        # 发送请求
        response = requests.get(url, headers=headers)
        
        # 检查响应状态
        if response.status_code != 200:
            raise Exception(f"API请求失败，状态码: {response.status_code}, 响应: {response.text}")
            
        # 解析JSON响应
        response_data = response.json()
        
        # 检查API返回状态
        if response_data.get("error_code") != 0:
            error_msg = response_data.get("reason", "未知错误")
            raise Exception(f"查询失败: {error_msg}")
            
        # 提取严重违法信息
        illegal_data = response_data.get("result", {})
        items_list = illegal_data.get("items", [])
        total = illegal_data.get("total", 0)
        
        # 构建格式化信息
        illegal_info = []
        for item in items_list:
            illegal_entry = {
                "列入原因": item.get("putReason"),
                "列入日期": self._format_timestamp(item.get("putDate")),
                "列入机关": item.get("putDepartment"),
                "移除原因": item.get("removeReason") or "尚未移除",
                "移除日期": self._format_timestamp(item.get("removeDate")) or "尚未移除",
                "移除机关": item.get("removeDepartment") or "尚未移除"
            }
            illegal_info.append(illegal_entry)
            
        result = {
            "严重违法": {
                "总记录数": total,
                "当前页": page_num,
                "每页数量": page_size,
                "违法记录": illegal_info
            }
        }
        
        if not illegal_info:
            result["严重违法"]["说明"] = "未查询到该企业的严重违法信息"
            
        return result