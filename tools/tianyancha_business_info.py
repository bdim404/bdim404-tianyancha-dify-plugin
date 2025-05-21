from collections.abc import Generator
from typing import Any
import requests
from datetime import datetime

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

class TianyanchaBusinessInfoTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        获取企业工商信息
        
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
        
        # 调用API获取工商信息
        try:
            result = self._get_company_business_info(company_keyword, token)
            
            # 仅返回结构化JSON数据
            yield self.create_json_message(result)
        except Exception as e:
            error_message = f"请求过程中发生错误: {str(e)}"
            yield self.create_json_message({"error": error_message})
        
    def _format_timestamp(self, timestamp):
        """格式化时间戳为可读日期"""
        if not timestamp:
            return "未知"
        try:
            # 毫秒时间戳转为秒
            if len(str(timestamp)) > 10:
                timestamp = int(timestamp) / 1000
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            return str(timestamp)
            
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