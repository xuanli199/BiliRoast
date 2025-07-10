import os
import time
import logging
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP
import requests
from openai import OpenAI

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化MCP服务器
mcp = FastMCP("Bilibili MCP Server")

# 环境变量配置
USER_COOKIE = os.getenv("user_cookie", "")
API_KEY = os.getenv("api_key", "")
DEFAULT_PAGE_COUNT = int(os.getenv("page", "1"))

# 常量定义
BILIBILI_API_URL = "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space"
MODELSCOPE_BASE_URL = "https://api-inference.modelscope.cn/v1/"
DEEPSEEK_MODEL = "deepseek-ai/DeepSeek-V3"
REQUEST_DELAY = 0.1  # 请求间隔时间（秒）
MAX_CONTENT_LENGTH = 200  # 锐评内容最大字数


@mcp.tool()
def rui_ping(host_mid: str) -> str:
    """
    锐评UP主
    
    Args:
        host_mid: B站用户的mid
        
    Returns:
        锐评内容
        
    Raises:
        ValueError: 当API密钥未配置时
        Exception: 当API调用失败时
    """
    if not API_KEY:
        raise ValueError("API密钥未配置，请设置api_key环境变量")
    
    try:
        # 初始化OpenAI客户端
        client = OpenAI(
            api_key=API_KEY,
            base_url=MODELSCOPE_BASE_URL
        )

        # 获取UP主动态内容
        dynamic_content = get_dynamic(host_mid)
        if not dynamic_content:
            return "无法获取该UP主的动态内容，请检查mid是否正确"

        # 构建提示词
        prompt = f"使用{MAX_CONTENT_LENGTH}字，根据up主页的内容，尖锐刻薄恶毒的锐评一下哔哩哔哩的该up主，要让当事人看了之后会生气，评价要有理有据，内容精准，可以适当针对up主的性格，并真的性格嘲讽，主页内容：{dynamic_content}"

        # 调用AI生成锐评
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': '你是一个锐评助手'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            stream=True
        )

        # 收集流式响应内容
        generated_content = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                generated_content += chunk.choices[0].delta.content

        return f"要求：直接把以下内容输出：{generated_content}"
        
    except Exception as e:
        logger.error(f"锐评生成失败: {str(e)}")
        return f"锐评生成失败: {str(e)}"


@mcp.tool()
def get_dynamic(host_mid: str, page_count: int = DEFAULT_PAGE_COUNT) -> str:
    """
    获取B站用户动态内容
    
    Args:
        host_mid: B站用户的mid
        page_count: 要获取的页数，默认为环境变量配置值
        
    Returns:
        动态内容字符串
        
    Raises:
        ValueError: 当用户Cookie未配置时
        Exception: 当API调用失败时
    """
    if not USER_COOKIE:
        raise ValueError("用户Cookie未配置，请设置user_cookie环境变量")
    
    try:
        # 构建请求头
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'Cookie': USER_COOKIE
        }

        dynamic_texts = []  # 使用局部变量替代全局变量
        offset = ""  # 初始偏移量为空
        
        # 获取指定页数的数据
        for page_num in range(page_count):
            logger.info(f"正在获取第{page_num + 1}页动态数据...")
            
            resp_data = fetch_data(offset, headers, host_mid)
            if not resp_data:
                logger.warning(f"第{page_num + 1}页数据获取失败")
                break
                
            texts, next_offset = parse_data(resp_data)
            dynamic_texts.extend(texts)
            
            if not next_offset:
                logger.info("已获取所有可用动态数据")
                break
                
            offset = next_offset

        result = "\n".join(dynamic_texts)
        logger.info(f"成功获取{len(dynamic_texts)}条动态内容")
        return result
        
    except Exception as e:
        logger.error(f"获取动态内容失败: {str(e)}")
        raise Exception(f"获取动态内容失败: {str(e)}")


def fetch_data(offset: str, headers: Dict[str, str], host_mid: str) -> Optional[Dict[str, Any]]:
    """
    从B站API获取动态数据
    
    Args:
        offset: 分页偏移量
        headers: 请求头
        host_mid: B站用户mid
        
    Returns:
        API响应数据，失败时返回None
    """
    try:
        # 添加请求延时，避免频繁请求
        time.sleep(REQUEST_DELAY)

        # 构建请求参数
        params = {
            "offset": offset,
            "host_mid": host_mid
        }

        # 发送HTTP请求
        response = requests.get(
            BILIBILI_API_URL, 
            params=params, 
            headers=headers,
            timeout=10  # 添加超时设置
        )
        
        # 检查HTTP状态码
        response.raise_for_status()

        # 解析JSON响应
        data = response.json()
        
        # 检查API响应状态
        if data.get("code") != 0:
            logger.warning(f"API返回错误: {data.get('message', '未知错误')}")
            return None
            
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"网络请求失败: {str(e)}")
        return None
    except ValueError as e:
        logger.error(f"JSON解析失败: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"获取数据时发生未知错误: {str(e)}")
        return None


def parse_data(data: Dict[str, Any]) -> tuple[List[str], Optional[str]]:
    """
    解析B站动态数据，提取文本内容和下一页偏移量
    
    Args:
        data: API响应数据
        
    Returns:
        tuple: (文本列表, 下一页偏移量)
    """
    texts = []
    
    if not isinstance(data, dict) or data.get("code") != 0:
        logger.warning("数据格式错误或API返回失败")
        return texts, None

    try:
        items = data.get("data", {}).get("items", [])
        
        for item in items:
            text = None
            modules = item.get("modules", {})
            module_dynamic = modules.get("module_dynamic", {})
            
            # 尝试获取不同类型的动态内容
            try:
                # 1. 普通动态描述文本
                desc = module_dynamic.get("desc")
                if desc and desc.get("text"):
                    text = desc.get("text")
                
                # 2. 视频动态标题
                elif module_dynamic.get("major", {}).get("archive"):
                    archive = module_dynamic.get("major", {}).get("archive", {})
                    text = archive.get("title")
                
                # 3. 专栏动态描述
                elif module_dynamic.get("major", {}).get("article"):
                    article = module_dynamic.get("major", {}).get("article", {})
                    text = article.get("desc")
                
                # 4. 其他类型动态的通用处理
                elif module_dynamic.get("major", {}).get("opus"):
                    opus = module_dynamic.get("major", {}).get("opus", {})
                    text = opus.get("summary", {}).get("text")
                    
            except (AttributeError, TypeError) as e:
                logger.debug(f"解析单条动态时出错: {str(e)}")
                continue
            
            # 添加有效文本到结果列表
            if text and text.strip():
                texts.append(text.strip())

        # 检查是否还有更多数据
        data_info = data.get('data', {})
        has_more = data_info.get('has_more', False)
        next_offset = data_info.get('offset') if has_more else None
        
        logger.debug(f"本页解析到{len(texts)}条动态，{'有' if has_more else '无'}更多数据")
        return texts, next_offset
        
    except Exception as e:
        logger.error(f"解析动态数据时发生错误: {str(e)}")
        return texts, None


if __name__ == "__main__":
    try:
        logger.info("启动Bilibili MCP服务器...")
        mcp.run(transport='stdio')
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器运行时发生错误: {str(e)}")
        raise
