from collections.abc import Generator
from typing import Any
import requests
import os
from datetime import datetime

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

class TianyanchaDifyPluginTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        获取企业相关信息
        
        参数:
            tool_parameters: 包含查询参数的字典
                - company_keyword: 公司关键词(名称或ID)
                - query_type: 查询类型(基本信息/司法风险/工商信息)
        """
        # 获取参数
        company_keyword = tool_parameters.get("company_keyword")
        query_type = tool_parameters.get("query_type", "基本信息")
        
        if not company_keyword:
            yield self.create_json_message({
                "error": "公司关键词不能为空"
            })
            return
            
        # 从runtime获取凭证
        try:
            token = self.runtime.credentials["token"]
        except (KeyError, AttributeError):
            yield self.create_json_message({
                "error": "API token未配置，请在插件设置中提供有效的天眼查API Token"
            })
            return
        
        # 根据查询类型调用不同API
        try:
            if query_type == "司法风险":
                result = self._get_company_judicial_risk(company_keyword, token)
            elif query_type == "工商信息":
                result = self._get_company_business_info(company_keyword, token)
            else:  # 默认为基本信息
                result = self._get_company_base_info(company_keyword, token)
                
            yield self.create_json_message(result)
        except Exception as e:
            yield self.create_json_message({
                "error": f"请求过程中发生错误: {str(e)}"
            })
    
    def _get_company_base_info(self, company_keyword: str, token: str) -> dict:
        """
        获取企业基本信息的API调用实现
        
        参数:
            company_keyword: 公司关键词
            token: API凭证
            
        返回:
            格式化后的企业基本信息
        """
        # 构建请求
        url = f"http://open.api.tianyancha.com/services/open/ic/baseinfo/normal?keyword={company_keyword}"
        headers = {'Authorization': token}
        
        # 发送请求
        response = requests.get(url, headers=headers)
        
        # 检查响应状态
        if response.status_code != 200:
            raise Exception(f"API请求失败，状态码: {response.status_code}, 响应: {response.text}")
            
        # 解析JSON响应
        response_data = response.json()
        
        # 检查API返回状态
        if response_data.get("error_code") != 0 or not response_data.get("result"):
            error_msg = response_data.get("reason", "未知错误")
            raise Exception(f"查询失败: {error_msg}")
            
        # 提取企业基本信息字段
        company_data = response_data.get("result", {})
        
        # 构建格式化信息
        return {
            "基本信息": {
                "公司名称": company_data.get("name"),
                "英文名称": company_data.get("property3"),
                "公司别名": company_data.get("alias"),
                "法定代表人": company_data.get("legalPersonName"),
                "企业类型": company_data.get("companyOrgType"),
                "注册资本": f"{company_data.get('regCapital')}",
                "实缴资本": f"{company_data.get('actualCapital')}",
                "成立日期": self._format_timestamp(company_data.get("estiblishTime")),
                "经营状态": company_data.get("regStatus"),
                "统一社会信用代码": company_data.get("creditCode"),
                "工商注册号": company_data.get("regNumber"),
                "组织机构代码": company_data.get("orgNumber"),
                "纳税人识别号": company_data.get("taxNumber"),
                "所属行业": company_data.get("industry"),
                "行业细分": company_data.get("industryAll", {})
            },
            "注册信息": {
                "登记机关": company_data.get("regInstitute"),
                "注册地址": company_data.get("regLocation"),
                "经营范围": company_data.get("businessScope"),
                "营业期限": f"{self._format_timestamp(company_data.get('fromTime'))} 至 {self._format_timestamp(company_data.get('toTime'))}"
            },
            "企业标签": company_data.get("tags", "").split(";") if company_data.get("tags") else []
        }
    
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
    
    def _get_company_business_info(self, company_keyword: str, token: str) -> dict:
        """
        获取企业工商信息的API调用实现
        
        参数:
            company_keyword: 公司关键词
            token: API凭证
            
        返回:
            格式化后的企业工商信息
        """
        # 构建请求
        url = f"http://open.api.tianyancha.com/services/open/cb/ic/2.0?keyword={company_keyword}"
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
            
        # 提取工商信息
        business_data = response_data.get("result", {})
        
        # 构建格式化信息
        result = {"工商信息": {}}
        
        # 基本信息部分
        basic_info = {
            "公司名称": business_data.get("name"),
            "注册资本": business_data.get("regCapital"),
            "实缴资本": business_data.get("actualCapital"),
            "成立日期": self._format_timestamp(business_data.get("estiblishTime")),
            "统一社会信用代码": business_data.get("creditCode"),
            "工商注册号": business_data.get("regNumber"),
            "企业类型": business_data.get("companyOrgType"),
            "经营状态": business_data.get("regStatus"),
            "法定代表人": business_data.get("legalPersonName"),
            "注册地址": business_data.get("regLocation"),
            "登记机关": business_data.get("regInstitute"),
            "经营范围": business_data.get("businessScope")
        }
        result["工商信息"]["基本信息"] = basic_info
        
        # 主要人员
        staff_list = business_data.get("staffList", [])
        if staff_list:
            staff_info = []
            for staff in staff_list:
                staff_info.append({
                    "姓名": staff.get("name"),
                    "职位": staff.get("staffTypeName"),
                    "其他职位": staff.get("typeJoin", [])
                })
            result["工商信息"]["主要人员"] = staff_info
        
        # 股东信息
        shareholder_list = business_data.get("shareHolderList", [])
        if shareholder_list:
            shareholder_info = []
            for shareholder in shareholder_list:
                capital_info = []
                for capital in shareholder.get("capital", []):
                    capital_info.append({
                        "出资额": capital.get("amomon"),
                        "出资比例": capital.get("percent"),
                        "出资方式": capital.get("paymet"),
                        "出资时间": capital.get("time")
                    })
                
                shareholder_info.append({
                    "股东名称": shareholder.get("name"),
                    "股东类型": "自然人" if shareholder.get("type") == 2 else "企业",
                    "资本信息": capital_info
                })
            result["工商信息"]["股东信息"] = shareholder_info
        
        # 对外投资
        invest_list = business_data.get("investList", [])
        if invest_list:
            investment_info = []
            for invest in invest_list[:10]:  # 只取前10个投资,避免数据过多
                investment_info.append({
                    "被投资企业名称": invest.get("name"),
                    "被投资企业简称": invest.get("alias"),
                    "投资比例": invest.get("percent"),
                    "投资金额": invest.get("amount"),
                    "注册资本": invest.get("regCapital"),
                    "经营状态": invest.get("regStatus"),
                    "成立日期": self._format_timestamp(invest.get("estiblishTime")),
                    "所属行业": invest.get("category")
                })
            result["工商信息"]["对外投资"] = investment_info
            
            # 如果投资公司超过10个,添加提示
            if len(invest_list) > 10:
                result["工商信息"]["对外投资_说明"] = f"该企业共有{len(invest_list)}家对外投资企业,仅展示前10家"
        
        # 分支机构
        branch_list = business_data.get("branchList", [])
        if branch_list:
            branch_info = []
            for branch in branch_list[:10]:  # 只取前10个分支机构,避免数据过多
                branch_info.append({
                    "分支机构名称": branch.get("name"),
                    "分支机构简称": branch.get("alias"),
                    "登记状态": branch.get("regStatus"),
                    "成立日期": self._format_timestamp(branch.get("estiblishTime")),
                    "负责人": branch.get("legalPersonName")
                })
            result["工商信息"]["分支机构"] = branch_info
            
            # 如果分支机构超过10个,添加提示
            if len(branch_list) > 10:
                result["工商信息"]["分支机构_说明"] = f"该企业共有{len(branch_list)}家分支机构,仅展示前10家"
        
        # 变更记录
        change_list = business_data.get("changeList", [])
        if change_list:
            change_info = []
            for change in change_list[:10]:  # 只取前10个变更记录,避免数据过多
                change_info.append({
                    "变更项目": change.get("changeItem"),
                    "变更时间": change.get("changeTime"),
                    "变更前内容": change.get("contentBefore"),
                    "变更后内容": change.get("contentAfter")
                })
            result["工商信息"]["变更记录"] = change_info
            
            # 如果变更记录超过10个,添加提示
            if len(change_list) > 10:
                result["工商信息"]["变更记录_说明"] = f"该企业共有{len(change_list)}条变更记录,仅展示前10条"
            
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
    
    def _format_timestamp(self, timestamp):
        """
        将时间戳转换为可读格式的日期
        
        参数:
            timestamp: 毫秒级时间戳
            
        返回:
            格式化的日期字符串
        """
        if not timestamp:
            return "未知"
        try:
            # 天眼查时间戳是毫秒级的
            return datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d')
        except:
            return str(timestamp)
