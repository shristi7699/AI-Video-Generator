import asyncio

class RateLimiter:
    def __init__(self, max_concurrent: int = 2):
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def acquire(self):
        await self.semaphore.acquire()

    def release(self):
        self.semaphore.release()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.release()

# Global rate limiter for heavy tasks like video generation
video_rate_limiter = RateLimiter(max_concurrent=2)
