# API Sender 插件

从外部URL获取随机图片并发送到聊天中，支持多种图片源和自定义API。

## 功能特性

- 🎨 多源随机图片（萌图、壁纸、ACG等）
- 🔗 支持自定义URL获取图片
- 📡 支持JSON API解析获取图片
- 🤖 LLM工具集成（大模型可直接调用获取图片）

## 指令列表

| 指令 | 参数 | 说明 |
|------|------|------|
| `/一图` | 无 | 从默认源获取随机萌图 |
| `/来张` | `[分类]` | 从指定分类获取图片 |
| `/图url` | `[url]` | 从指定URL获取图片 |
| `/图json` | `[api_url] [json_path]` | 从JSON API解析并获取图片 |

## 使用示例

 '''
 
 /一图 /来张 moe /来张 pc /图url https://example.com/image.jpg /图json https://api.example.com/random-image url /图json https://api.example.com/random-image data.image.url
 
 '''

## 支持的图片分类

| 分类 | 说明 | 默认URL |
|------|------|---------|
| `moe` | 萌图/二次元 | https://t.alcy.cc/moe |
| `pc` | 电脑壁纸 | https://t.alcy.cc/pc |
| `mobile` | 手机壁纸 | https://t.alcy.cc/moemp4 |
| `acg` | ACG图片 | https://www.loliapi.com/acg/ |

## LLM工具支持

本插件为LLM提供了两个工具函数，大模型在对话中可以直接调用：

### 1. get_random_image
获取随机图片URL，适用于用户想看随机图片的场景。

**参数：**
- `category` (string): 图片分类，可选值：moe、pc、mobile、acg

### 2. fetch_image_from_api
从JSON API获取图片URL，适用于用户提供了特定API的场景。

**参数：**
- `api_url` (string): JSON API的URL地址
- `json_path` (string): JSON中图片URL的字段路径（默认"url"）

## 安装要求

- AstrBot >= v4.0.0
- Python >= 3.10
- 依赖：`aiohttp>=3.8.0`

## 注意事项

- 部分图片源可能需要翻墙访问
- 自定义URL需以 `http://` 或 `https://` 开头
- JSON API返回的数据格式需包含图片URL字段

## 作者

- 作者：月凌
- 版本：1.0.0
