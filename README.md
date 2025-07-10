# BiliRoast

锐评哔哩哔哩up主。


## 使用方法

1. clone 项目代码。

```
git clone https://github.com/xuanli199/BiliRoast
```

或者到 [https://github.com/xuanli199/BiliRoast](https://github.com/xuanli199/BiliRoast) 下载代码。

2. 使用 uv 安装项目依赖。

```bash
uv sync
```

3. 在 mcp client 中配置 Server。

```json
{
  "mcpServers": {
    "bilibili": {
      "name": "bilibili",
      "type": "stdio",
      "isActive": true,
      "registryUrl": "",
      "tags": [],
      "command": "uv",
      "args": [
        "--directory",
        "/项目本地位置/BiliRoast",
        "run",
        "bilibili.py"
      ],
      "env": {
        "user_cookie": "获取cookie：buvid3=xxx; b_nut=xxx; _uuid=xxx;",
        "api_key": "魔搭社区key",
        "page": "1"
      }
    }
  }
}
```

## 获取参数

1.获取cookie

访问哔哩哔哩网页版，按`f12`打开控制台，选择网络（network），查看控制台中的请求。在标头中查看是否包含`cookie`，如果不包含就换一个请求。如果包含，就复制前三部分内容`buvid3=xxx; b_nut=xxx; _uuid=xxx;`。

![image](https://github.com/user-attachments/assets/eb177688-f9d1-4fa7-9750-60c77ded1dd1)


2.获取key

打开魔搭社区，获取key[https://www.modelscope.cn/my/myaccesstoken](https://www.modelscope.cn/my/myaccesstoken)

3.page

page参数为爬取动态内容页面，默认为1。

