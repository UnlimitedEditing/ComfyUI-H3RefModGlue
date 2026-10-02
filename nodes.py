"""Glue for Luisacaotica/ComfyUI-MiniMaxH3Mod on ephemeral Graydient runners.

The upstream Load H3 RefMods node takes its mod names from a COMBO dropdown that
is built from models/refmods at startup, and its VALIDATE_INPUTS rejects any name
not already on disk. malcolmrey/minimaxh3 hosts ~1,700 tiny (~1.5 MB) refmods, so
pre-downloading them all, or a fixed handful via concept_mapping, defeats the
point. This node takes plain STRING names, fetches each file from the HF repo on
demand (a second or less), then delegates to the real MiniMaxH3RefModsLoader.load()
so token budgeting, strength handling and bundle loading stay upstream's.
"""
import os

import folder_paths
import requests

HF_BASE = "https://huggingface.co/malcolmrey/minimaxh3/resolve/main/"
MAX_MODS = 3


def _full_name(name):
    """'alanrickman' -> 'minimaxh3_alanrickman_v1_refmod'; full names pass through."""
    name = name.strip()
    if name.endswith(".safetensors"):
        name = name[: -len(".safetensors")]
    if name.startswith("minimaxh3_"):
        return name
    if name.endswith("_refmod"):
        return "minimaxh3_" + name
    return f"minimaxh3_{name}_v1_refmod"


def _fetch(full):
    dest_dir = os.path.join(folder_paths.models_dir, "refmods")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, full + ".safetensors")
    if os.path.isfile(dest) and os.path.getsize(dest) > 0:
        return
    r = requests.get(HF_BASE + full + ".safetensors", timeout=60)
    if r.status_code != 200:
        raise ValueError(f"RefMod '{full}' not found on malcolmrey/minimaxh3 (HTTP {r.status_code})")
    tmp = dest + ".part"
    with open(tmp, "wb") as f:
        f.write(r.content)
    os.replace(tmp, dest)


class H3RefModFetchLoad:
    @classmethod
    def INPUT_TYPES(cls):
        req = {}
        for i in range(1, MAX_MODS + 1):
            req[f"refmod_{i}"] = ("STRING", {"default": "", "multiline": False,
                "tooltip": "Name on malcolmrey/minimaxh3, e.g. alanrickman or "
                           "minimaxh3_alanrickman_v1_refmod. Empty = unused."})
        req["strength"] = ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01})
        req["copies"] = ("INT", {"default": 1, "min": 1, "max": 10})
        return {"required": req}

    RETURN_TYPES = ("H3_REF_MODS", "STRING")
    RETURN_NAMES = ("mods", "prompt_hint")
    FUNCTION = "run"
    CATEGORY = "MiniMax-H3/mod"

    def run(self, strength=1.0, copies=1, **kw):
        import nodes as comfy_nodes
        loader_cls = comfy_nodes.NODE_CLASS_MAPPINGS.get("MiniMaxH3RefModsLoader")
        if loader_cls is None:
            raise RuntimeError("ComfyUI-MiniMaxH3Mod is not installed (MiniMaxH3RefModsLoader missing)")
        args = {"show_info": False}
        slot = 0
        for i in range(1, MAX_MODS + 1):
            n = (kw.get(f"refmod_{i}") or "").strip()
            if not n:
                continue
            slot += 1
            full = _full_name(n)
            _fetch(full)
            args[f"mod_{slot}"] = full
            args[f"strength_{slot}"] = float(strength)
            args[f"copies_{slot}"] = int(copies)
        if slot == 0:
            raise ValueError("H3RefModFetchLoad: give at least one refmod name")
        for i in range(slot + 1, loader_cls.MAX_SLOTS + 1):
            args[f"mod_{i}"] = loader_cls.NONE
        return loader_cls().load(**args)


NODE_CLASS_MAPPINGS = {"H3RefModFetchLoad": H3RefModFetchLoad}
NODE_DISPLAY_NAME_MAPPINGS = {"H3RefModFetchLoad": "H3 RefMod Fetch + Load"}
