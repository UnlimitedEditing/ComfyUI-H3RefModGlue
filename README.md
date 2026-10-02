# ComfyUI-H3RefModGlue

Glue for [Luisacaotica/ComfyUI-MiniMaxH3Mod](https://github.com/Luisacaotica/ComfyUI-MiniMaxH3Mod) on ephemeral runners.

`H3 RefMod Fetch + Load` takes plain STRING names (e.g. `alanrickman`), downloads each
`minimaxh3_<name>_v1_refmod.safetensors` from `malcolmrey/minimaxh3` into `models/refmods`
on demand, then delegates to the upstream `MiniMaxH3RefModsLoader.load()`. Needed because the
upstream loader is a COMBO validated against files already on disk.

Requires ComfyUI-MiniMaxH3Mod installed alongside.
