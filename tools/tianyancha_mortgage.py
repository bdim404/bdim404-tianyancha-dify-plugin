from collections.abc import Generator
from typing import Any
import requests
from datetime import datetime

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

class TianyanchaMortgageTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        获取企业动产抵押公告信息
        
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
        
        # 调用API获取动产抵押信息
        try:
            result = self._get_company_mortgage_info(company_keyword, token, page_size, page_num)
            
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
    
    def _get_company_mortgage_info(self, company_keyword: str, token: str, page_size: int = 20, page_num: int = 1) -> dict:
        """
        获取企业动产抵押信息的API调用实现
        
        参数:
            company_keyword: 公司关键词
            token: API凭证
            page_size: 每页数据量
            page_num: 页码
            
        返回:
            格式化后的企业动产抵押信息
        """
        # 构建请求
        url = f"http://open.api.tianyancha.com/services/open/mr/mortgageInfo/2.0?keyword={company_keyword}&pageSize={page_size}&pageNum={page_num}"
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
            
        # 提取动产抵押信息
        mortgage_data = response_data.get("result", {})
        items_list = mortgage_data.get("items", [])
        total = mortgage_data.get("total", 0)
        
        # 构建格式化信息
        mortgage_info = []
        for item in items_list:
            base_info = item.get("baseInfo", {})
            people_info = item.get("peopleInfo", [])
            pawn_info_list = item.get("pawnInfoList", [])
            change_info_list = item.get("changeInfoList", [])
            
            mortgage_entry = {
                "基本信息": {
                    "登记编号": base_info.get("regNum"),
                    "登记日期": base_info.get("regDate"),
                    "登记机关": base_info.get("regDepartment"),
                    "状态": base_info.get("status"),
                    "被担保债权种类": base_info.get("type"),
                    "担保金额": base_info.get("amount"),
                    "债权期限": base_info.get("term") or base_info.get("overviewTerm"),
                    "担保范围": base_info.get("scope") or base_info.get("overviewScope"),
                    "注销日期": base_info.get("cancelDate"),
                    "注销原因": base_info.get("cancelReason"),
                    "公示日期": self._format_timestamp(base_info.get("publishDate")),
                    "备注": base_info.get("remark") or base_info.get("overviewRemark")
                },
                "债权人信息": [
                    {
                        "名称": person.get("peopleName"),
                        "证件类型": person.get("liceseType"),
                        "证件号码": person.get("licenseNum")
                    } for person in people_info
                ],
                "抵押物信息": [
                    {
                        "抵押物名称": pawn.get("pawnName"),
                        "所有权归属": pawn.get("ownership"),
                        "数量及状况": pawn.get("detail"),
                        "备注": pawn.get("remark")
                    } for pawn in pawn_info_list
                ],
                "变更信息": [
                    {
                        "变更日期": change.get("changeDate"),
                        "变更内容": change.get("changeContent")
                    } for change in change_info_list
                ]
            }
            mortgage_info.append(mortgage_entry)
            
        result = {
            "动产抵押": {
                "总记录数": total,
                "当前页": page_num,
                "每页数量": page_size,
                "抵押记录": mortgage_info
            }
        }
        
        if not mortgage_info:
            result["动产抵押"]["说明"] = "未查询到该企业的动产抵押信息"
            
        return result