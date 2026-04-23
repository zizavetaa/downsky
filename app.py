import os
import random
import pygame
import asyncio
import websockets
from aiohttp import web
from http import HTTPStatus
import io
import base64
import threading
import constants as constants
from PIL import Image

from parse import Parser
from image_utils import RandomIndexSampler, PatchImage

port = os.getenv("PORT", 10000)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
img_width = 624
img_height = 696

comments_path = 'downdetector_comments_new.txt'

orig_path = 'sky_cut.png'
original = pygame.image.load(orig_path)

class Animator:
    def __init__(self, bx, by):
        self.resx = 624 
        self.resy = 696 
        self.texts = []
        self.texts_only = []
        self.frame_lock = threading.Lock()
        self.latest_frame = None
        self.done = False
        self.first_run = True
        self.clock = pygame.time.Clock()
        self.parser = Parser()
        self.patch_image = PatchImage(cols=bx, rows=by, orig_path=orig_path)
        self.num_patches = bx*by
        self.displayed_patches = 0
        with open(comments_path) as f:
            self.comments = f.readlines()
        self.idx_sampler = RandomIndexSampler(self.num_patches)
        self.pos_sampler = RandomIndexSampler(self.num_patches)
        self.image = Image.new("RGB", (img_width, img_height), (255, 255, 255))

    def handle_external_events(self):
        if not self.parser.event_queue.empty():
            event = self.parser.event_queue.get()

            if event:
                self.image = self.generate_image()
                self.write_comment(event)
    
    def start_parser(self):
        thread = threading.Thread(target=self.parser.parse, daemon=True)
        thread.start()
    
    def wrap_text(self, text, max_width):
        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            text_surface = self.font.render(test_line, True, (0, 0, 0))

            if text_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:  # push current line
                    lines.append(current_line)
                current_line = word  # start new line

        if current_line:
            lines.append(current_line)

        return lines
    
    def render_multiline(self, text, max_width):
        lines = self.wrap_text(text, max_width)

        line_surfaces = [self.font.render(line, True, (0, 0, 0)) for line in lines]

        width = max(s.get_width() for s in line_surfaces)
        height = sum(s.get_height() for s in line_surfaces)

        surface = pygame.Surface((width, height), pygame.SRCALPHA)

        y_offset = 0
        for s in line_surfaces:
            surface.blit(s, (0, y_offset))
            y_offset += s.get_height()

        return surface
    
    def write_comment(self, text):
        self.texts_only.append(text)
        text_surface = self.render_multiline(text, self.resx)

        x = random.randint(0, self.resx - text_surface.get_width())
        y = random.randint(0, self.resy - text_surface.get_height())
        self.texts.append((text_surface, (x,y)))
    
    def generate_image(self,):
        patch_index = self.idx_sampler.sample()
        position_index = self.pos_sampler.sample()
        patch = self.patch_image.get_patch(patch_index)
        left, upper, _, _ = self.patch_image.get_patch_coords(position_index)
        new_img = self.patch_image.add_patch(self.image, patch, left, upper)
        self.displayed_patches += 1
        return new_img
    
    def pil_to_pygame_img(self, pil_image):
        mode = pil_image.mode
        size = pil_image.size
        data = pil_image.tobytes()
        pygame_image = pygame.image.fromstring(data, size, mode)
        return pygame_image
    
    def draw(self):
        self.screen.fill(constants.WHITE)
        pygame_img = self.pil_to_pygame_img(self.image)
        pygame_img = pygame.transform.scale(pygame_img, (img_width, img_height))
        self.screen.blit(pygame_img, (self.resx, 0))
        for t, pos in self.texts:
            self.screen.blit(t, pos)
        pygame.display.flip()
        with self.frame_lock:
            self.latest_frame = pygame.display.get_surface()
    
    def reset(self):
        self.texts.clear()
        self.texts_only.clear()
        self.image = Image.new("RGB", (img_width, img_height), (255, 255, 255))
        self.idx_sampler = RandomIndexSampler(self.num_patches)
        self.pos_sampler = RandomIndexSampler(self.num_patches)
        self.displayed_patches = 0
        self.first_run = True
    
    def run(self):
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 10)
        self.screen = pygame.display.set_mode((self.resx*2,self.resy))
        self.start_parser()

        last_check = 0
        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if len(self.texts) == 0:
                            text = 'не робит'
                            self.write_comment(text)
                        else:
                            idx_max = len(self.texts)
                            idx = random.randint(0, idx_max - 1)
                            self.image = self.generate_image()
                            self.write_comment(self.texts_only[idx])

            if self.first_run:
                self.image = self.generate_image()
                text = 'не робит'
                self.write_comment(text)
                self.first_run = False

            now = pygame.time.get_ticks()
            if now - last_check > 5:
                self.handle_external_events()
                self.draw()
                self.clock.tick(10)
                last_check = now
                if self.displayed_patches == self.num_patches - 1:
                    self.reset()
        pygame.font.quit()
        pygame.display.quit()  

def start_server(game):
    clients = set()

    async def send_frames(game):
        while not game.done:

            with game.frame_lock:
                if game.latest_frame is None:
                    await asyncio.sleep(0.01)
                    continue
                frame = game.latest_frame.copy()

            # pil_image = Image.fromarray(frame)
            data = pygame.image.tostring(frame, "RGB")
            pil_image = Image.frombytes("RGB", frame.get_size(), data)

            with io.BytesIO() as byte_io:
                pil_image.save(byte_io, format="PNG")
                base64_image = base64.b64encode(byte_io.getvalue()).decode()
            # --- broadcast ---
            dead_clients = set()
            async def send(ws):
            # for ws in clients:
                try:
                    if ws.closed:
                        dead_clients.add(ws)
                        return
                    await ws.send_str(base64_image)
                except Exception:
                    dead_clients.add(ws)

            await asyncio.gather(*(send(ws) for ws in clients), return_exceptions=True)
            # cleanup disconnected clients
            for ws in dead_clients:
                # clients.remove(ws)
                clients.discard(ws)
            await asyncio.sleep(0.1)


    async def websocket_handler(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        clients.add(ws)

        try:
            async for msg in ws:
                pass  # you can handle incoming messages here if needed
        finally:
            # clients.remove(ws)
            clients.discarfd(ws)
            print(f"Client disconnected. Total: {len(clients)}")
        
        return ws

    async def index(request):
        return web.FileResponse("index.html")
    
    async def start_background_tasks(app):
        app["sender_task"] = asyncio.create_task(send_frames(app["game"]))
    
    async def cleanup_background_tasks(app):
        app["sender_task"].cancel()
        try:
            await app["sender_task"]
        except asyncio.CancelledError:
            pass
    
    # async def cleanup_background_tasks(app):
    #     app["sender_task"].cancel()
    #     await app["sender_task"]

    app = web.Application()
    app["game"] = game
    app.router.add_get("/", index)
    app.router.add_get("/ws", websocket_handler)

    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    web.run_app(app, host="0.0.0.0", port=10000, handle_signals=False)

def main():
    animator = Animator(20,34)

    server_thread = threading.Thread(
        target=start_server,
        args=(animator,),
        daemon=True
    )
    server_thread.start()
    animator.run()

    server_thread.join()

if __name__ == "__main__":
    main()
