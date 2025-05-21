from collections.abc import Generator
from typing import Any
import requests
from datetime import datetime

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

class TianyanchaJudicialRiskTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        获取企业司法风险信息
        
        参数:
            tool_parameters: 包含查询参数的字典
                - company_keyword: 公司关键词(名称或ID)
        """
        # 获取参数
        company_keyword = tool_parameters.get("company_keyword")
        
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
        
        # 调用API获取司法风险信息
        try:
            result = self._get_company_judicial_risk(company_keyword, token)
            
            # 仅返回结构化JSON数据
            yield self.create_json_message(result)
        except Exception as e:
            error_message = f"请求过程中发生错误: {str(e)}"
            yield self.create_json_message({"error": error_message})
        
    def _get_company_judicial_risk(self, company_keyword: str, token: str) -> dict:
        """
        获取企业司法风险信息的API调用实现
        
        参数:
            company_keyword: 公司关键词
            token: API凭证
            
        返回:
            格式化后的企业司法风险信息
        """
        # 构建请求
        url = f"http://open.api.tianyancha.com/services/open/cb/judicial/2.0?keyword={company_keyword}"
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
            
        # 提取司法风险信息
        judicial_data = response_data.get("result", {})
        
        # 构建格式化信息
        result = {"司法风险": {}}
        
        # 法律诉讼
        lawsuit_list = judicial_data.get("lawSuitList", [])
        if lawsuit_list:
            result["司法风险"]["法律诉讼"] = [self._format_lawsuit(item) for item in lawsuit_list]
        
        # 开庭公告
        kt_announcement_list = judicial_data.get("ktAnnouncementList", [])
        if kt_announcement_list:
            result["司法风险"]["开庭公告"] = [self._format_kt_announcement(item) for item in kt_announcement_list]
        
        # 被执行人
        zhixing_list = judicial_data.get("zhixingList", [])
        if zhixing_list:
            result["司法风险"]["被执行人"] = [self._format_zhixing(item) for item in zhixing_list]
        
        # 法院公告
        court_announcement_list = judicial_data.get("courtAnnouncementList", [])
        if court_announcement_list:
            result["司法风险"]["法院公告"] = [self._format_court_announcement(item) for item in court_announcement_list]
        
        # 立案信息
        court_register_list = judicial_data.get("courtRegisterList", [])
        if court_register_list:
            result["司法风险"]["立案信息"] = [self._format_court_register(item) for item in court_register_list]
        
        # 送达公告
        send_announcement_list = judicial_data.get("sendAnnouncementList", [])
        if send_announcement_list:
            result["司法风险"]["送达公告"] = [self._format_send_announcement(item) for item in send_announcement_list]
        
        # 失信人
        dishonest_list = judicial_data.get("dishonestList", [])
        if dishonest_list:
            result["司法风险"]["失信人"] = [self._format_dishonest(item) for item in dishonest_list]
        
        # 如果没有任何司法风险数据
        if not result["司法风险"]:
            result["司法风险"] = "未查询到该企业的司法风险信息"
            
        return result
    
    def _format_lawsuit(self, item: dict) -> dict:
        """格式化法律诉讼信息"""
        return {
            "案件编号": item.get("caseno"),
            "案件标题": item.get("title"),
            "案由": item.get("casereason"),
            "案件类型": item.get("casetype"),
            "法院": item.get("court"),
            "文书类型": item.get("doctype"),
            "提交时间": item.get("submittime"),
            "裁判时间": item.get("judgetime"),
            "原告": item.get("plaintiffs"),
            "被告": item.get("defendants"),
            "案件链接": item.get("lawsuitUrl")
        }
        
    def _format_kt_announcement(self, item: dict) -> dict:
        """格式化开庭公告信息"""
        return {
            "案件编号": item.get("caseNo"),
            "案由": item.get("caseReason"),
            "法院": item.get("court"),
            "开庭日期": item.get("startDate"),
            "法庭": item.get("courtroom"),
            "当事人": item.get("litigant")
        }
    
    def _format_zhixing(self, item: dict) -> dict:
        """格式化被执行人信息"""
        return {
            "案件编号": item.get("caseCode"),
            "执行法院": item.get("execCourtName"),
            "立案时间": item.get("caseCreateTime"),
            "执行标的": item.get("execMoney")
        }
    
    def _format_court_announcement(self, item: dict) -> dict:
        """格式化法院公告信息"""
        return {
            "案件编号": item.get("caseno"),
            "当事人1": item.get("party1"),
            "当事人2": item.get("party2"),
            "案由": item.get("reason"),
            "法院": item.get("courtcode"),
            "公告类型": item.get("bltntypename"),
            "公告日期": item.get("publishdate"),
            "内容摘要": item.get("content")[:100] + "..." if len(item.get("content", "")) > 100 else item.get("content")
        }
    
    def _format_court_register(self, item: dict) -> dict:
        """格式化立案信息"""
        return {
            "案件编号": item.get("caseNo"),
            "立案日期": item.get("filingDate"),
            "法院": item.get("court"),
            "原告": item.get("plaintiff"),
            "被告": item.get("defendant"),
            "案由": item.get("caseReason") or "未公开"
        }
    
    def _format_send_announcement(self, item: dict) -> dict:
        """格式化送达公告信息"""
        return {
            "标题": item.get("title"),
            "法院": item.get("court"),
            "公告日期": item.get("startDate"),
            "内容摘要": item.get("content")[:100] + "..." if len(item.get("content", "")) > 100 else item.get("content")
        }
    
    def _format_dishonest(self, item: dict) -> dict:
        """格式化失信人信息"""
        return {
            "案件编号": item.get("casecode"),
            "失信人名称": item.get("iname"),
            "执行法院": item.get("courtname"),
            "地区": item.get("areaname"),
            "立案日期": item.get("regdate"),
            "公布日期": item.get("publishdate"),
            "失信行为": item.get("disrupttypename"),
            "履行情况": item.get("performance"),
            "义务": item.get("duty")
        }