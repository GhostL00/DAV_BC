import streamlit as st
import hashlib
import json
import os
import pandas as pd
from datetime import datetime
from PIL import Image
import base64
from io import BytesIO

# -------------------- Blockchain Classes --------------------
class Block:
    def __init__(self, index, timestamp, art_hash, owner, metadata, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.art_hash = art_hash
        self.owner = owner
        self.metadata = metadata
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, str(datetime.now()), "0", "Genesis", {"title":"Genesis Block"}, "0")
        self.chain.append(genesis_block)

    def add_block(self, art_hash, owner, metadata):
        previous_block = self.chain[-1]
        new_block = Block(len(self.chain), str(datetime.now()), art_hash, owner, metadata, previous_block.hash)
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
                    block_data['owner'],
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

# -------------------- Streamlit App --------------------
st.set_page_config(page_title="NFT Blockchain Simulator", layout="wide")
st.title("🎨 NFT Blockchain Simulator")
st.write("Mint and verify digital art NFTs stored in a blockchain.")

# Load blockchain
blockchain = Blockchain.load()

# Tabs
mint_tab, verify_tab, explorer_tab, stats_tab = st.tabs(["🎨 Mint NFT", "🔍 Verify NFT", "📜 Blockchain Explorer", "📊 Statistics"])

# -------------------- Mint NFT --------------------
with mint_tab:
    st.header("Mint a New NFT")
    with st.form("mint_form"):
        uploaded_file = st.file_uploader("Upload your artwork", type=["png", "jpg", "jpeg"])
        owner = st.text_input("Enter Owner Name/Wallet")
        title = st.text_input("Artwork Title")
        description = st.text_area("Description")
        category = st.selectbox("Category", ["Art", "Photography", "Collectible", "Other"])
        submitted = st.form_submit_button("Mint NFT")

    if submitted and uploaded_file and owner:
        art_hash, img_bytes = get_image_hash(uploaded_file)
        metadata = {"title": title, "description": description, "category": category,
                    "thumbnail": create_thumbnail(img_bytes)}
        new_block = blockchain.add_block(art_hash, owner, metadata)
        blockchain.save()
        st.success(f"NFT minted successfully in Block #{new_block.index}!")

# -------------------- Verify NFT --------------------
with verify_tab:
    st.header("Verify NFT Ownership")
    file_to_verify = st.file_uploader("Upload artwork to verify", type=["png", "jpg", "jpeg"], key="verify")
    if file_to_verify:
        art_hash, _ = get_image_hash(file_to_verify)
        matches = [block for block in blockchain.chain if block.art_hash == art_hash]
        if matches:
            st.success("This artwork exists on the blockchain!")
            for block in matches:
                st.write(f"✅ Block #{block.index} | Owner: {block.owner} | Title: {block.metadata.get('title')}")
        else:
            st.error("❌ This artwork does not exist in the blockchain.")

# -------------------- Blockchain Explorer --------------------
with explorer_tab:
    st.header("Blockchain Explorer")

    chain_data = []
    for block in blockchain.chain:
        chain_data.append({
            "Index": block.index,
            "Timestamp": block.timestamp,
            "Owner": block.owner,
            "Title": block.metadata.get("title"),
            "Category": block.metadata.get("category"),
            "Hash": block.hash,
            "Thumbnail": f'<img src="data:image/png;base64,{block.metadata.get("thumbnail", "")}" width="50">'
        })

    df = pd.DataFrame(chain_data)
    st.write("### Blockchain Table")
    st.write(df.to_html(escape=False), unsafe_allow_html=True)

    st.write("### Integrity Check")
    if blockchain.is_chain_valid():
        st.success("✅ Blockchain is valid!")
    else:
        st.error("❌ Blockchain integrity compromised!")

# -------------------- Statistics Tab --------------------
with stats_tab:
    st.header("NFT Statistics & Leaderboard")
    total_nfts = len(blockchain.chain) - 1  # exclude genesis
    unique_owners = set(block.owner for block in blockchain.chain[1:])

    st.write(f"**Total NFTs Minted:** {total_nfts}")
    st.write(f"**Unique Owners:** {len(unique_owners)}")

    # Top creators leaderboard
    owner_counts = {}
    for block in blockchain.chain[1:]:
        owner_counts[block.owner] = owner_counts.get(block.owner, 0) + 1
    leaderboard = pd.DataFrame(sorted(owner_counts.items(), key=lambda x: x[1], reverse=True), columns=["Owner", "NFTs Minted"])

    st.write("### Top NFT Creators")
    st.dataframe(leaderboard)
