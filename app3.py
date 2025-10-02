import streamlit as st
import hashlib
import json
import os
import pandas as pd
from datetime import datetime
from PIL import Image
import base64
from io import BytesIO
from ecdsa import SigningKey, SECP256k1, VerifyingKey
import plotly.express as px

# -------------------- Blockchain Classes --------------------
class Block:
    def __init__(self, index, timestamp, art_hash, owner_name, owner_pubkey, signature, metadata, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.art_hash = art_hash
        self.owner_name = owner_name
        self.owner_pubkey = owner_pubkey
        self.signature = signature
        self.metadata = metadata
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.compute_hash()

    def compute_hash(self):
        # Exclude the stored hash itself when computing to avoid false integrity errors
        block_dict = self.__dict__.copy()
        block_dict.pop('hash', None)
        return hashlib.sha256(json.dumps(block_dict, sort_keys=True).encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, str(datetime.now()), "0", "Genesis", None, None, {"title":"Genesis Block"}, "0")
        self.chain.append(genesis_block)

    def add_block(self, art_hash, owner_name, owner_pubkey, signature, metadata):
        previous_block = self.chain[-1]
        new_block = Block(len(self.chain), str(datetime.now()), art_hash, owner_name, owner_pubkey, signature, metadata, previous_block.hash)
        self.chain.append(new_block)
        return new_block

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            prev = self.chain[i - 1]
            curr = self.chain[i]
            if curr.hash != curr.compute_hash():
                return False
            if curr.previous_hash != prev.hash:
                return False
        return True

    def to_dict(self):
        return [block.__dict__ for block in self.chain]

    def save(self, filename="blockchain.json"):
        with open(filename, "w") as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def load(cls, filename="blockchain.json"):
        if os.path.exists(filename):
            with open(filename, "r") as f:
                data = json.load(f)
            blockchain = cls()
            blockchain.chain = []
            for block_data in data:
                block = Block(
                    block_data['index'],
                    block_data['timestamp'],
                    block_data['art_hash'],
                    block_data['owner_name'],
                    block_data.get('owner_pubkey'),
                    block_data.get('signature'),
                    block_data['metadata'],
                    block_data['previous_hash']
                )
                block.nonce = block_data.get('nonce', 0)
                block.hash = block_data['hash']
                blockchain.chain.append(block)
            return blockchain
        return cls()

# -------------------- Utility Functions --------------------
def get_image_hash(image):
    img_bytes = image.read()
    return hashlib.sha256(img_bytes).hexdigest(), img_bytes

def create_thumbnail(image_bytes):
    img = Image.open(BytesIO(image_bytes))
    img.thumbnail((100, 100))
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def generate_wallet():
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.verifying_key
    return sk, vk

def sign_art(sk: SigningKey, art_hash: str) -> str:
    signature = sk.sign(art_hash.encode())
    return base64.b64encode(signature).decode()

def verify_signature(vk: VerifyingKey, art_hash: str, signature: str) -> bool:
    try:
        return vk.verify(base64.b64decode(signature), art_hash.encode())
    except:
        return False

# -------------------- Streamlit App --------------------
st.set_page_config(page_title="NFT Blockchain Simulator", layout="wide")
st.title("🎨 NFT Blockchain Simulator")
st.write("Mint and verify digital art NFTs stored in a blockchain with wallet addresses and signatures.")

# Load blockchain
blockchain = Blockchain.load()

# Tabs
mint_tab, verify_tab, explorer_tab, stats_tab = st.tabs(["🎨 Mint NFT", "🔍 Verify NFT", "📜 Blockchain Explorer", "📊 Statistics"])

# The rest of your app (minting, verifying, explorer, stats) remains unchanged.
