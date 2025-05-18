from typing import Any
import requests

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class TianyanchaDifyPluginProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            # 获取token
            token = credentials.get("token")
            print(f"token: {token}")
            if not token:
                raise ToolProviderCredentialValidationError("API token不能为空")
                
            # 进行一个简单的API调用来验证token
            url = "http://open.api.tianyancha.com/services/open/ic/baseinfo/normal?keyword=北京百度网讯科技有限公司"
            headers = {'Authorization': token}
            
            response = requests.get(url, headers=headers)
            
            # 验证响应
            if response.status_code != 200:
                raise ToolProviderCredentialValidationError(f"API验证失败，状态码: {response.status_code}")
                
            # 检查API返回结果
            response_data = response.json()
            if response_data.get("error_code") != 0:
                error_msg = response_data.get("reason", "未知错误")
                raise ToolProviderCredentialValidationError(f"API验证失败: {error_msg}")
                
        except ToolProviderCredentialValidationError:
            # 直接重新抛出自定义的验证错误
            raise
        except Exception as e:
            # 处理其他可能的错误
            raise ToolProviderCredentialValidationError(f"凭证验证失败: {str(e)}")
