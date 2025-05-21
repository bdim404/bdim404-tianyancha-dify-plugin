from collections.abc import Generator
from typing import Any
import requests
from datetime import datetime

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

class TianyanchaPublicNoticeTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        获取企业票据公示催告信息
        
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
        
        # 调用API获取公示催告信息
        try:
            result = self._get_company_public_notice(company_keyword, token, page_size, page_num)
            
            # 返回结构化JSON数据
            yield self.create_json_message(result)
        except Exception as e:
            error_message = f"请求过程中发生错误: {str(e)}"
            yield self.create_json_message({"error": error_message})
    
    def _get_company_public_notice(self, company_keyword: str, token: str, page_size: int = 20, page_num: int = 1) -> dict:
        """
        获取企业票据公示催告信息的API调用实现
        
        参数:
            company_keyword: 公司关键词
            token: API凭证
            page_size: 每页数据量
            page_num: 页码
            
        返回:
            格式化后的企业票据公示催告信息
        """
        # 构建请求
        url = f"http://open.api.tianyancha.com/services/v4/open/publicNotice?keyword={company_keyword}&pageSize={page_size}&pageNum={page_num}"
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
            
        # 提取公示催告信息
        notice_data = response_data.get("result", {})
        items_list = notice_data.get("items", [])
        total = notice_data.get("total", 0)
        
        # 构建格式化信息
        notice_info = []
        for item in items_list:
            notice_entry = {
                "票据类型": item.get("billType"),
                "票据号码": item.get("billNum"),
                "票面金额": item.get("billAmt"),
                "票据开始日期": item.get("billBeginDt"),
                "票据结束日期": item.get("billEndDt") or "未公示",
                "紧急类型": item.get("exigentType"),
                "公告日期": item.get("publishDt"),
                "发布机构": item.get("publishOrgName"),
                "出票人公司名称": item.get("drawCompanyName"),
                "出票人公司ID": item.get("drawCompanyId"),
                "持票人公司名称": item.get("ownerCompanyName"),
                "持票人公司ID": item.get("ownerCompanyId"),
                "申请人公司名称": item.get("applyCompanyName"),
                "申请人公司ID": item.get("applyCompanyId"),
                "付款银行": item.get("payCompanyName"),
                "详细公告内容": item.get("infoDetail")
            }
            notice_info.append(notice_entry)
            
        result = {
            "公示催告": {
                "总记录数": total,
                "当前页": page_num,
                "每页数量": page_size,
                "催告记录": notice_info
            }
        }
        
        if not notice_info:
            result["公示催告"]["说明"] = "未查询到该企业的票据公示催告信息"
            
        return result