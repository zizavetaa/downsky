import random
from PIL import Image

class RandomIndexSampler:
    def __init__(self, n):
        self.indices = list(range(n))
        random.shuffle(self.indices)

    def sample(self):
        if not self.indices:
            raise ValueError("No more indices left")
        return self.indices.pop()
    
    def return_idx(self, idx):
        self.indices.append(idx)
        random.shuffle(self.indices)

class PatchImage:
    def __init__(self, cols=20, rows=34, orig_path='sky3.png'):
        self.cols = cols
        self.rows = rows
        self.orig_image = Image.open(orig_path)

    def get_patch_coords(self, i):
        assert 0 <= i < self.cols * self.rows, "Index out of range" 
        img_width, img_height = self.orig_image.size

        patch_w = img_width // self.cols
        patch_h = img_height // self.rows
        row = i // self.cols
        col = i % self.cols

        left = col * patch_w
        upper = row * patch_h
        right = left + patch_w
        lower = upper + patch_h
        return left, upper, right, lower

    def get_patch(self, i):
        # Coordinates
        left, upper, right, lower = self.get_patch_coords(i)
        patch = self.orig_image.crop((left, upper, right, lower))
        return patch

    def add_patch(self, img, patch, left, upper):
        img.paste(patch, (left, upper))
        return img

    def remove_patch(self, img,  i):
        assert 0 <= i < self.cols * self.rows, "Index out of range" 
        img_width, img_height = self.orig_image.size

        patch_w = img_width // self.cols
        patch_h = img_height // self.rows

        # Row and column of the patch
        row = i // self.cols
        col = i % self.cols

        # Coordinates
        left = col * patch_w
        upper = row * patch_h
        right = left + patch_w
        lower = upper + patch_h

        white_image = Image.new("RGB", (img_width, img_height), (255, 255, 255))
        anti_patch = white_image.crop((left, upper, right, lower))
        img.paste(anti_patch, (left, upper))
        return img