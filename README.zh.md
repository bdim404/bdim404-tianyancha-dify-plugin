# 天眼查 Dify 插件

[English Documentation](./README.md)

一个用于集成天眼查企业信息查询功能的Dify插件。

## 关于天眼查

天眼查是中国知名的企业信息查询平台，提供企业工商信息、司法风险、经营状况、知识产权等多维度的企业信息查询服务。该平台通过整合多个政府部门的公开数据，为用户提供全面、准确的企业信息。

您可以访问[天眼查官网](https://www.tianyancha.com/)了解更多信息。

## 使用方法

### 安装

您可以下载[最新发布版本](https://github.com/bdim404/tianyancha-dify-plugin/releases/latest)并上传到Dify平台，详细操作请参考[安装和使用插件：本地文件上传](https://docs.dify.ai/zh-CN/plugins/quick-start/install-plugins#local-file-upload)。

### 打包（可选）

如果您想自行打包此插件，请确保已安装[dify-plugin-daemon](https://github.com/langgenius/dify-plugin-daemon/releases)，然后下载或使用`git clone`克隆此仓库，之后可以通过以下命令打包：

```
dify-plugin-daemon plugin package ./tianyancha-dify-plugin
```

有关更多信息，请参阅[工具插件：打包插件](https://docs.dify.ai/zh-CN/plugins/quick-start/develop-plugins/tool-plugin#packing-plugin)。

### 设置授权

安装插件后，您需要配置与天眼查API的连接。

您需要提供以下凭证：

- **API Token**: 用于访问天眼查开放API的授权令牌

您可以在[天眼查开放平台](https://open.tianyancha.com/)申请并获取API Token。在数据中心 -> 我的接口页面可以查看您的Token信息。

在设置过程中，插件将验证您的凭证，确保能够成功连接到天眼查API服务。

完成授权设置后，您就可以使用此插件与天眼查API进行交互。

### 功能

本插件支持以下功能：

1. **基本信息查询**：查询企业的基础工商注册信息，包括企业名称、注册资本、成立日期、法定代表人、经营范围等。

2. **工商信息查询**：查询企业的详细工商信息，包括股东信息、主要人员、对外投资、分支机构、变更记录等。

3. **司法风险查询**：查询企业的司法风险信息，包括法律诉讼、法院公告、开庭公告、失信人、被执行人等。

您可以在Dify的工作流或其他地方调用此插件，所有参数都有详细注释说明。只需提供公司名称或ID，并选择需要查询的信息类型即可获取相应结果。

## 作者

**作者:** bdim, fernvenue  
**版本:** 0.1.0
**类型:** tool
