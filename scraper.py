import asyncio
import random
import yt_dlp
import aiohttp
import re
from typing import Dict, Any

class AntiBan:
    def __init__(self):
        # User-Agent ro'yxati (Anti-ban uchun)
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
        ]
        # Agar proksilar bo'lsa, shu yerga qo'shing
        self.proxies = [
            # "http://user:pass@ip:port",
        ]

    def get_random_ua(self):
        return random.choice(self.user_agents)

    def get_random_proxy(self):
        return random.choice(self.proxies) if self.proxies else None

class LinkedinScraper:
    def __init__(self):
        self.anti_ban = AntiBan()

    async def get_media_only(self, url: str) -> Dict[str, Any]:
        """API uchun asosiy funksiya."""
        result = await asyncio.to_thread(self._extract_with_ytdlp, url)
        
        # Agar yt-dlp yordamida topilmasa yoki faqat rasm bo'lsa, HTML parser orqali urinib ko'ramiz
        if not result.get("success") or not result.get("media"):
            fallback_result = await self._fallback_html_parser(url)
            if fallback_result.get("success"):
                return fallback_result
                
        return result

    def _extract_with_ytdlp(self, url: str) -> Dict[str, Any]:
        proxy = self.anti_ban.get_random_proxy()
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'allowed_extractors': ['linkedin'],
            'http_headers': {
                'User-Agent': self.anti_ban.get_random_ua()
            }
        }
        if proxy:
            ydl_opts['proxy'] = proxy
            
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return {"success": False, "error": "Media topilmadi."}

                media_list = []
                if info.get('url'):
                    media_list.append({
                        "type": "video" if info.get('ext') == 'mp4' else "image",
                        "url": info.get('url'),
                        "quality": f"{info.get('width', 0)}x{info.get('height', 0)}",
                        "title": info.get('title', '')
                    })
                
                formats = info.get('formats', [])
                if formats:
                    best_format = sorted(formats, key=lambda x: x.get('width', 0) or 0, reverse=True)[0]
                    if best_format.get('url') and best_format.get('url') != info.get('url'):
                         media_list.append({
                            "type": "video",
                            "url": best_format.get('url'),
                            "quality": f"{best_format.get('width', 0)}x{best_format.get('height', 0)}",
                            "title": info.get('title', '')
                        })

                # yt-dlp dagi rasmlarni ham olamiz (thumbnail)
                if info.get('thumbnail'):
                    media_list.append({
                        "type": "image",
                        "url": info.get('thumbnail'),
                        "title": "Thumbnail / Image"
                    })

                return {
                    "success": True,
                    "media": media_list,
                    "title": info.get('title', ''),
                    "author": info.get('uploader', '')
                }
        except Exception as e:
            err_msg = str(e)
            if "404" in err_msg or "Not Found" in err_msg:
                return {"success": False, "error": "LinkedIn anonim so'rovni blokladi (404/Login talab etiladi). IP/Proxy almashtiring."}
            return {"success": False, "error": err_msg}

    async def _fallback_html_parser(self, url: str) -> Dict[str, Any]:
        """Rasmlar yoki hujjarlarni olish uchun qo'shimcha usul (HTML metadata orqali)."""
        headers = {
            "User-Agent": self.anti_ban.get_random_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        proxy = self.anti_ban.get_random_proxy()
        
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, proxy=proxy, timeout=10) as response:
                    html = await response.text()
                    
                    if response.status == 200 or response.status == 999: # 999 is LinkedIn's specific code
                        media_list = []
                        # OpenGraph rasm
                        og_image = re.search(r'<meta property="og:image" content="(.*?)"', html)
                        if og_image:
                            media_list.append({
                                "type": "image",
                                "url": og_image.group(1).replace("&amp;", "&"),
                                "title": "OpenGraph Image"
                            })
                            
                        og_title = re.search(r'<meta property="og:title" content="(.*?)"', html)
                        title = og_title.group(1) if og_title else ""
                        
                        if media_list:
                            return {
                                "success": True,
                                "media": media_list,
                                "title": title,
                                "author": "Unknown"
                            }
                    
                    return {"success": False, "error": f"Fallback parser failed with status {response.status}"}
        except Exception as e:
            return {"success": False, "error": f"Fallback error: {str(e)}"}
