import aiohttp
import json
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp


@register("astrbot_plugin_api_sender", "月凌", "从外部URL获取随机图片并发送到聊天中", "1.0.0")
class RandomImagePlugin(Star):
    """随机图片插件 - 从外部URL获取图片并发送"""
    
    # 默认图片URL配置
    DEFAULT_IMAGE_URLS = {
        "moe": "https://t.alcy.cc/moe",
        "pc": "https://t.alcy.cc/pc",
        "mobile": "https://t.alcy.cc/moemp4",
        "acg": "https://www.loliapi.com/acg/"
    }
    
    def __init__(self, context: Context, config: dict = None) -> None:
        super().__init__(context)
        
        # 使用 AstrBot 配置系统
        if config:
            self.image_urls = config.get("image_urls", self.DEFAULT_IMAGE_URLS)
            self.timeout = config.get("timeout", 30)
        else:
            self.image_urls = self.DEFAULT_IMAGE_URLS
            self.timeout = 30
    
    @filter.command("一图")
    async def random_image(self, event: AstrMessageEvent):
        """
        从默认URL获取随机图片并发送
        使用示例: /一图
        """
        try:
            # 使用默认的moe接口
            url = self.image_urls.get("moe", "https://t.alcy.cc/moe")
            
            # 构建消息链：文字 + 图片
            chain = [
                Comp.Plain("为你找到一张随机图片~"),
                Comp.Image.fromURL(url)
            ]
            
            yield event.chain_result(chain)
            logger.info(f"已发送图片: {url}")
            
        except Exception as e:
            logger.error(f"获取图片失败: {e}")
            yield event.plain_result(f"获取图片失败，请稍后重试: {str(e)}")
    
    @filter.command("来张")
    async def specific_image(self, event: AstrMessageEvent, category: str = "moe"):
        """
        从指定分类获取图片
        使用示例: /来张 moe 或 /来张 pc 或 /来张 acg
        """
        try:
            # 检查分类是否存在
            if category not in self.image_urls:
                available = ", ".join(self.image_urls.keys())
                yield event.plain_result(f"未知的分类: {category}\n可用分类: {available}")
                return
            
            url = self.image_urls[category]
            
            # 构建消息链
            chain = [
                Comp.Plain(f"为你找到一张 [{category}] 图片~"),
                Comp.Image.fromURL(url)
            ]
            
            yield event.chain_result(chain)
            logger.info(f"已发送 [{category}] 图片: {url}")
            
        except Exception as e:
            logger.error(f"获取图片失败: {e}")
            yield event.plain_result(f"获取图片失败: {str(e)}")
    
    @filter.command("图url")
    async def image_from_url(self, event: AstrMessageEvent, url: str):
        """
        从指定URL获取图片
        使用示例: /图url https://example.com/image.jpg
        """
        try:
            if not url.startswith(("http://", "https://")):
                yield event.plain_result("请提供有效的URL（以http://或https://开头）")
                return
            
            chain = [
                Comp.Plain("正在获取图片..."),
                Comp.Image.fromURL(url)
            ]
            
            yield event.chain_result(chain)
            logger.info(f"已从自定义URL发送图片: {url}")
            
        except Exception as e:
            logger.error(f"获取图片失败: {e}")
            yield event.plain_result(f"获取图片失败: {str(e)}")
    
    @filter.command("图json")
    async def image_from_json(self, event: AstrMessageEvent, api_url: str, json_path: str = "url"):
        """
        从JSON API获取图片URL并发送
        使用示例: /图json https://api.example.com/random-image url
        json_path: JSON中图片URL的字段路径，默认为"url"
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=self.timeout) as resp:
                    if resp.status != 200:
                        yield event.plain_result(f"API请求失败，状态码: {resp.status}")
                        return
                    
                    data = await resp.json()
                    
                    # 解析JSON路径获取图片URL
                    image_url = self._get_value_by_path(data, json_path)
                    
                    if image_url is None:
                        yield event.plain_result(f"JSON路径解析失败: {json_path}")
                        return
                    
                    if not isinstance(image_url, str):
                        yield event.plain_result(f"获取到的值不是有效的字符串URL")
                        return
                    
                    chain = [
                        Comp.Plain(f"从API获取到图片~"),
                        Comp.Image.fromURL(image_url)
                    ]
                    
                    yield event.chain_result(chain)
                    logger.info(f"已从JSON API发送图片: {image_url}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"网络请求失败: {e}")
            yield event.plain_result(f"网络请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"处理失败: {e}")
            yield event.plain_result(f"处理失败: {str(e)}")
    
    @filter.command("解析json")
    async def parse_json(self, event: AstrMessageEvent, api_url: str, json_path: str = ""):
        """
        从API获取JSON数据并解析指定路径的内容
        使用示例: 
        /解析json https://api.example.com/data
        /解析json https://api.example.com/data users.0.name
        /解析json https://api.example.com/data meta.total_count
        """
        try:
            if not api_url.startswith(("http://", "https://")):
                yield event.plain_result("请提供有效的URL（以http://或https://开头）")
                return
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=self.timeout) as resp:
                    if resp.status != 200:
                        yield event.plain_result(f"API请求失败，状态码: {resp.status}")
                        return
                    
                    data = await resp.json()
                    
                    # 如果没有指定路径，返回完整JSON
                    if not json_path:
                        formatted = json.dumps(data, ensure_ascii=False, indent=2)
                        # 如果内容太长，截断显示
                        if len(formatted) > 2000:
                            formatted = formatted[:2000] + "\n... (内容已截断)"
                        yield event.plain_result(f"完整JSON数据:\n```json\n{formatted}\n```")
                        return
                    
                    # 解析指定路径
                    result = self._get_value_by_path(data, json_path)
                    
                    if result is None:
                        yield event.plain_result(f"路径 '{json_path}' 未找到数据")
                        return
                    
                    # 格式化输出
                    if isinstance(result, (dict, list)):
                        formatted = json.dumps(result, ensure_ascii=False, indent=2)
                        if len(formatted) > 2000:
                            formatted = formatted[:2000] + "\n... (内容已截断)"
                        yield event.plain_result(f"路径 '{json_path}' 的数据:\n```json\n{formatted}\n```")
                    else:
                        yield event.plain_result(f"路径 '{json_path}' 的值: {result}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"网络请求失败: {e}")
            yield event.plain_result(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            yield event.plain_result(f"返回的数据不是有效的JSON格式")
        except Exception as e:
            logger.error(f"处理失败: {e}")
            yield event.plain_result(f"处理失败: {str(e)}")
    
    def _get_value_by_path(self, data: dict, path: str):
        """
        根据点号分隔的路径从嵌套字典中获取值
        
        Args:
            data: 字典数据
            path: 点号分隔的路径，如 "users.0.name"
        
        Returns:
            找到的值，如果路径不存在则返回None
        """
        if not path:
            return data
        
        current = data
        keys = path.split(".")
        
        for key in keys:
            if isinstance(current, dict):
                if key not in current:
                    return None
                current = current[key]
            elif isinstance(current, list):
                try:
                    index = int(key)
                    if index < 0 or index >= len(current):
                        return None
                    current = current[index]
                except ValueError:
                    return None
            else:
                return None
        
        return current
    
    @filter.llm_tool(name="send_random_image")
    async def send_random_image_tool(self, event: AstrMessageEvent, category: str = "moe"):
        '''
        发送随机图片到聊天。当用户想要看随机图片、二次元图片、ACG图片或需要图片素材时使用此工具。
        调用后会直接发送图片到聊天中，不需要在回复中再次发送图片链接。
        
        Args:
            category(string): 图片分类，可选值：moe(萌图/二次元)、pc(电脑壁纸)、mobile(手机壁纸)、acg(ACG图片)。默认为moe。
        
        Returns:
            string: 发送结果描述，告知LLM图片已发送。
        '''
        try:
            # 检查分类是否存在
            if category not in self.image_urls:
                available = ", ".join(self.image_urls.keys())
                await event.send(event.plain_result(f"未知的分类: {category}，可用分类: {available}"))
                return f"分类错误，已告知用户可用分类：{available}"
            
            url = self.image_urls[category]
            
            # 直接发送图片到聊天
            chain = [
                Comp.Plain(f"为你找到一张 [{category}] 图片~"),
                Comp.Image.fromURL(url)
            ]
            await event.send(event.chain_result(chain))
            logger.info(f"LLM工具已发送 [{category}] 图片: {url}")
            
            # 返回描述给LLM，让它知道图片已发送
            return f"已成功发送 {category} 分类的图片到聊天，图片URL: {url}。请在回复中告知用户图片已发送，不需要再次发送图片。"
            
        except Exception as e:
            logger.error(f"LLM工具发送图片失败: {e}")
            await event.send(event.plain_result(f"获取图片失败: {str(e)}"))
            return f"发送图片失败: {str(e)}，已告知用户错误信息。"
    
    @filter.llm_tool(name="send_image_from_api")
    async def send_image_from_api_tool(self, event: AstrMessageEvent, api_url: str, json_path: str = "url"):
        '''
        从JSON API获取并发送图片到聊天。当用户提供了特定的图片API接口或需要从自定义API获取图片时使用此工具。
        调用后会直接发送图片到聊天中，不需要在回复中再次发送。
        
        Args:
            api_url(string): JSON API的URL地址，必须是以http://或https://开头的完整URL。
            json_path(string): JSON响应中图片URL字段的路径，使用点号分隔嵌套字段，例如"data.image.url"。默认为"url"。
        
        Returns:
            string: 发送结果描述，告知LLM图片已发送或发送失败的原因。
        '''
        try:
            if not api_url.startswith(("http://", "https://")):
                await event.send(event.plain_result("请提供有效的URL（以http://或https://开头）"))
                return "错误：URL格式不正确，已告知用户。"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=self.timeout) as resp:
                    if resp.status != 200:
                        error_msg = f"API请求失败，状态码: {resp.status}"
                        await event.send(event.plain_result(error_msg))
                        return f"API请求失败: {resp.status}，已告知用户。"
                    
                    data = await resp.json()
                    
                    # 解析JSON路径获取图片URL
                    image_url = self._get_value_by_path(data, json_path)
                    
                    if image_url is None:
                        error_msg = f"JSON路径解析失败: {json_path}"
                        await event.send(event.plain_result(error_msg))
                        return f"JSON路径解析失败: {json_path}，已告知用户。"
                    
                    if not isinstance(image_url, str):
                        await event.send(event.plain_result("获取到的值不是有效的字符串URL"))
                        return "获取到的值不是有效的字符串URL，已告知用户。"
                    
                    # 直接发送图片到聊天
                    chain = [
                        Comp.Plain(f"从API获取到图片~"),
                        Comp.Image.fromURL(image_url)
                    ]
                    await event.send(event.chain_result(chain))
                    logger.info(f"LLM工具已从API发送图片: {image_url}")
                    
                    return f"已成功从API发送图片到聊天，图片URL: {image_url}。请在回复中告知用户图片已发送。"
                    
        except aiohttp.ClientError as e:
            logger.error(f"网络请求失败: {e}")
            await event.send(event.plain_result(f"网络请求失败: {str(e)}"))
            return f"网络请求失败: {str(e)}，已告知用户。"
        except Exception as e:
            logger.error(f"处理失败: {e}")
            await event.send(event.plain_result(f"处理失败: {str(e)}"))
            return f"处理失败: {str(e)}，已告知用户。"
    
    @filter.llm_tool(name="fetch_and_parse_json")
    async def fetch_and_parse_json_tool(self, event: AstrMessageEvent, api_url: str, json_path: str = ""):
        '''
        从API获取JSON数据并解析指定路径的内容。当需要获取API数据、查询信息、获取JSON中的特定字段时使用此工具。
        可以获取完整的JSON数据，也可以指定路径获取嵌套数据。
        
        Args:
            api_url(string): JSON API的URL地址，必须是以http://或https://开头的完整URL。
            json_path(string): 要获取的数据路径，使用点号分隔嵌套字段，例如"data.users.0.name"。
                             如果为空字符串，则返回完整的JSON数据。默认为空字符串。
        
        Returns:
            string: 获取到的数据内容，如果是复杂结构会格式化为JSON字符串。
        '''
        try:
            if not api_url.startswith(("http://", "https://")):
                await event.send(event.plain_result("请提供有效的URL（以http://或https://开头）"))
                return "错误：URL格式不正确，已告知用户。"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=self.timeout) as resp:
                    if resp.status != 200:
                        error_msg = f"API请求失败，状态码: {resp.status}"
                        await event.send(event.plain_result(error_msg))
                        return f"API请求失败，状态码: {resp.status}，已告知用户。"
                    
                    data = await resp.json()
                    
                    # 如果没有指定路径，返回完整JSON的摘要
                    if not json_path:
                        formatted = json.dumps(data, ensure_ascii=False, indent=2)
                        if len(formatted) > 1500:
                            formatted = formatted[:1500] + "\n... (内容已截断，完整数据请在对话中查看)"
                        
                        await event.send(event.plain_result(f"API返回的完整数据:\n```json\n{formatted}\n```"))
                        
                        data_type = type(data).__name__
                        if isinstance(data, dict):
                            keys = list(data.keys())[:5]
                            preview = f"包含字段: {', '.join(keys)}"
                            if len(data.keys()) > 5:
                                preview += f" 等共{len(data.keys())}个字段"
                        elif isinstance(data, list):
                            preview = f"包含{len(data)}个元素"
                        else:
                            preview = str(data)[:100]
                        
                        return f"已成功获取完整JSON数据（类型: {data_type}），{preview}。数据已发送到聊天中，请查看。"
                    
                    result = self._get_value_by_path(data, json_path)
                    
                    if result is None:
                        error_msg = f"路径 '{json_path}' 未找到数据"
                        await event.send(event.plain_result(error_msg))
                        return f"路径 '{json_path}' 未找到数据，已告知用户。"
                    
                    if isinstance(result, (dict, list)):
                        formatted = json.dumps(result, ensure_ascii=False, indent=2)
                        if len(formatted) > 1500:
                            formatted = formatted[:1500] + "\n... (内容已截断)"
                        
                        await event.send(event.plain_result(f"路径 '{json_path}' 的数据:\n```json\n{formatted}\n```"))
                        
                        # 返回描述给LLM
                        if isinstance(result, dict):
                            return f"成功获取路径 '{json_path}' 的数据（字典类型，包含{len(result)}个字段），数据已发送到聊天中。"
                        else:
                            return f"成功获取路径 '{json_path}' 的数据（列表类型，包含{len(result)}个元素），数据已发送到聊天中。"
                    else:
                        await event.send(event.plain_result(f"路径 '{json_path}' 的值: {result}"))
                        return f"成功获取路径 '{json_path}' 的值: {result}"
                    
        except aiohttp.ClientError as e:
            logger.error(f"网络请求失败: {e}")
            await event.send(event.plain_result(f"网络请求失败: {str(e)}"))
            return f"网络请求失败: {str(e)}，已告知用户。"
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            await event.send(event.plain_result("返回的数据不是有效的JSON格式"))
            return "返回的数据不是有效的JSON格式，已告知用户。"
        except Exception as e:
            logger.error(f"处理失败: {e}")
            await event.send(event.plain_result(f"处理失败: {str(e)}"))
            return f"处理失败: {str(e)}，已告知用户。"
    
    async def terminate(self):
        logger.info("API Sender插件已卸载")
