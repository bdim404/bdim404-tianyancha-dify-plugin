# Tianyancha Dify Plugin

[中文文档](./README.zh.md)

A Dify plugin for Tianyancha enterprise information query integration.

## About Tianyancha

Tianyancha is a well-known enterprise information query platform in China, providing multi-dimensional enterprise information query services including business registration information, judicial risks, operational status, intellectual property, and more. The platform integrates public data from multiple government departments to provide users with comprehensive and accurate enterprise information.

You can visit [Tianyancha official website](https://www.tianyancha.com/) for more information.

## Usage

### Install

You can download [the latest release](https://github.com/bdim404/tianyancha-dify-plugin/releases/latest) and upload it to the Dify platform. For detailed instructions, please refer to [Install and Use Plugins: Local File Upload](https://docs.dify.ai/plugins/quick-start/install-plugins#local-file-upload).

### Packing (Optional)

If you want to pack this plugin yourself, make sure you have [dify-plugin-daemon](https://github.com/langgenius/dify-plugin-daemon/releases) installed, and then download or `git clone` this repository. After that, you can pack it using the following command:

```
dify-plugin-daemon plugin package ./tianyancha-dify-plugin
```

For more information, please refer to [Tool Plugin: Packing Plugin](https://docs.dify.ai/plugins/quick-start/develop-plugins/tool-plugin#packing-plugin).

### Set Up Authorization

After installing the plugin, you need to configure the connection to the Tianyancha API.

You need to provide the following credential:

- **API Token**: Authorization token for accessing the Tianyancha Open API

You can apply for and obtain an API Token from the [Tianyancha Open Platform](https://open.tianyancha.com/). You can view your Token information on the Data Center -> My APIs page.

During the setup process, the plugin will verify your credentials to ensure that it can successfully connect to the Tianyancha API service.

Once the authorization setup is complete, you can interact with the Tianyancha API using this plugin.

### Features

This plugin supports the following features:

1. **Basic Information Query**: Query basic business registration information of enterprises, including enterprise name, registered capital, establishment date, legal representative, business scope, etc.

2. **Business Information Query**: Query detailed business information of enterprises, including shareholder information, key personnel, external investments, branch institutions, change records, etc.

3. **Judicial Risk Query**: Query judicial risk information of enterprises, including legal proceedings, court announcements, court hearing announcements, dishonest entities, persons subject to enforcement, etc.

You can call this plugin in Dify workflows or elsewhere. All parameters have detailed annotations. Simply provide the company name or ID and select the type of information you need to query to get the corresponding results.

## Author

**Author:** bdim, fernvenue  
**Version:** 0.0.2  
**Type:** tool
