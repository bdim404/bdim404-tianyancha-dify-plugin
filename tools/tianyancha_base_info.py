from collections.abc import Generator
from typing import Any
import requests
from datetime import datetime

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

class TianyanchaBaseInfoTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        获取企业基本信息
        
        参数:
            tool_parameters: 包含查询参数的字典
                - company_keyword: 公司关键词(名称或ID)
        """
        # 获取参数
        company_keyword = tool_parameters.get("company_keyword")
        
        if not company_keyword:
            error_message = "公司关键词不能为空"
            yield self.create_json_message({"error": error_message})
            yield self.create_text_message(error_message)
            return
            
        # 从runtime获取凭证
        try:
            token = self.runtime.credentials["token"]
        except (KeyError, AttributeError):
            error_message = "API token未配置，请在插件设置中提供有效的天眼查API Token"
            yield self.create_json_message({"error": error_message})
            yield self.create_text_message(error_message)
            return
        
        # 调用API获取基本信息
        try:
            result = self._get_company_base_info(company_keyword, token)
            text_result = self._generate_base_info_text(result)
            
            # 返回结构化JSON数据
            yield self.create_json_message(result)
            # 返回可读文本格式
            yield self.create_text_message(text_result)
        except Exception as e:
            error_message = f"请求过程中发生错误: {str(e)}"
            yield self.create_json_message({"error": error_message})
            yield self.create_text_message(error_message)
            
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
    
    def _generate_base_info_text(self, data: dict) -> str:
        """生成企业基本信息的可读文本"""
        basic_info = data.get("基本信息", {})
        reg_info = data.get("注册信息", {})
        tags = data.get("企业标签", [])
        
        text = f"# {basic_info.get('公司名称', '未知企业')}的基本信息\n\n"
        
        text += "## 基本信息\n"
        for key, value in basic_info.items():
            if value and key != "行业细分":  # 排除行业细分，因为它可能是复杂结构
                text += f"- **{key}**: {value}\n"
        
        text += "\n## 注册信息\n"
        for key, value in reg_info.items():
            if value:
                text += f"- **{key}**: {value}\n"
        
        if tags:
            text += "\n## 企业标签\n"
            text += "- " + "、".join(tags) + "\n"
        
        return text
    
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