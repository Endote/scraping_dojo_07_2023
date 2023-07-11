import asyncio
import jsonlines
import random

from dotenv import load_dotenv
from os import environ as env
from pyppeteer import launch

class QuotesScraper:
    def __init__(self, url, output, proxy=None):
        self.browser = None
        self.proxy = proxy
        self.url = url
        self.output = output

    async def scrape_website(self):
        launch_args = []
        if self.proxy:
            try:
                launch_args.append(f'--proxy-server={self.proxy}')
                self.browser = await launch(args=launch_args)
                page = await self.browser.newPage()
                await self.set_user_agent(page)
                await page.goto(self.url)
            except:
                launch_args = []
                self.browser = await launch(args=launch_args)
                page = await self.browser.newPage()
                await self.set_user_agent(page)
                await page.goto(self.url)
        else:
            self.browser = await launch(args=launch_args)
            page = await self.browser.newPage()
            await self.set_user_agent(page)
            await page.goto(self.url)

        await page.waitForSelector('.quote')

        quotes = await self.extract_quotes(page)

        await self.browser.close()

        self.save_quotes_to_file(quotes)

    async def set_user_agent(self, page):
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        ]
        user_agent = random.choice(user_agents)
        await page.setUserAgent(user_agent)

    async def extract_quotes(self, page):
        quotes = []

        while True:
            current_page_quotes = await page.evaluate('''() => {
                const quoteElements = document.querySelectorAll('.quote');
                const quotes = [];
                for (const element of quoteElements) {
                    const text = element.querySelector('.text').textContent.trim();
                    const by = element.querySelector('.author').textContent.trim();
                    const tags = Array.from(element.querySelectorAll('.tag')).map(tag => tag.textContent.trim());
                    quotes.push({ text, by, tags });
                }
                return quotes;
            }''')

            quotes.extend(current_page_quotes)

            next_button = await page.querySelector('.next')
            if next_button is None:
                break

            await next_button.click()
            await self.random_delay(1, 2) 

            await self.scroll_page(page)
            await self.random_delay(2, 4)  

            await page.waitForSelector('.quote')

        return quotes

    async def scroll_page(self, page):
        scroll_height = await page.evaluate('document.documentElement.scrollHeight')
        viewport_height = await page.evaluate('window.innerHeight')

        while scroll_height > 0:
            scroll_distance = random.randint(int(viewport_height / 2), viewport_height)
            await page.evaluate(f'window.scrollBy(0, {scroll_distance})')
            scroll_height -= scroll_distance

            await self.random_delay(1, 2)  

    async def random_delay(self, min_delay, max_delay):
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)

    def save_quotes_to_file(self, quotes):
        with jsonlines.open(self.output, mode='w') as writer:
            for quote in quotes:
                writer.write(quote)

if __name__ == '__main__':
    load_dotenv()
    u = env['INPUT_URL']
    o = env['OUTPUT_FILE']
    p = env['PROXY']

    scraper = QuotesScraper(u, o, p)

    asyncio.get_event_loop().run_until_complete(scraper.scrape_website())
