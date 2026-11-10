"""Iron Sights for Sniper Elite 4 - removes the telescopic sights from the scoped rifles and replaces the scope
view with an open-sight picture rendered from the rifle's own 3D model.

Needs only Python 3.8+ (standard library). Close the game before running.

  IronSights.exe  (or python IronSights.py)   menu: install / change rifle / uninstall
  python IronSights.py install RIFLE PAINT e.g.  install kar98k body
  python IronSights.py uninstall
  python IronSights.py status
  add  --game "D:\\Steam\\steamapps\\common\\Sniper Elite 4"   if the game is not found automatically

Uninstall puts every touched file back byte for byte. Only the original compressed blocks that get replaced are
kept (IronSights_backup folder inside the game folder), not whole copies of the 1.2 GB of archives.
"""
import hashlib, json, lzma, os, re, struct, sys, zlib

VERSION = '1.0.0'
FROZEN = getattr(sys, 'frozen', False)          # running as IronSights.exe (PyInstaller)
HERE = os.path.dirname(sys.executable if FROZEN else os.path.abspath(__file__))
SIGHTS = os.path.join(HERE, 'sights')
BACKUP_DIR = 'IronSights_backup'

# --------------------------------------------------------------------------------------------- rifle tables
# Scope models are separate meshes named <rifle>_scope..., <rifle>_<paint>_scope... (+ LODs l1#.. l4#);
# every archive holding a copy is listed (paint DLCs carry their own copies).
SCOPE_ARCHIVES = {'carcano': ['Misc\\Common.asr',
             'DLCData\\DLC_Weapon_CamoRiflesSP_Carcano.asr',
             'DLCData\\DLC_Weapon_ColdWarfareWinterEP_SnowCamoSkin_Carcano.asr',
             'DLCData\\DLC_Weapon_NightFighterEP_NightCamoSkin_Carcano.asr',
             'DLCData\\DLC_Weapon_UrbanAssaultEP_UrbanCamoSkin_Carcano.asr'],
 'delisle_carbine': ['Misc\\Common.asr', 'DLCData\\DLC_Weapon_SilentWarfareWP_DelisleCarbine.asr'],
 'g43': ['Misc\\Common.asr',
         'DLCData\\DLC_Weapon_CamoRiflesSP_G43.asr',
         'DLCData\\DLC_Weapon_ColdWarfareWinterEP_SnowCamoSkin_G43.asr',
         'DLCData\\DLC_Weapon_NightFighterEP_NightCamoSkin_G43.asr',
         'DLCData\\DLC_Weapon_UrbanAssaultEP_UrbanCamoSkin_G43.asr',
         'DLCData\\DLC_Weapon_ColdWarfareWinterEP_ZH-29.asr',
         'DLCData\\DLC_Weapon_ColdWarfareWinterEP_SnowCamoSkin_ZH-29.asr'],
 'kar98k': ['Misc\\Common.asr',
            'DLCData\\DLC_Weapon_CamoRiflesSP_Kar98K.asr',
            'DLCData\\DLC_Weapon_ColdWarfareWinterEP_SnowCamoSkin_Kar98k.asr',
            'DLCData\\DLC_Weapon_NightFighterEP_NightCamoSkin_Kar98k.asr',
            'DLCData\\DLC_Weapon_UrbanAssaultEP_UrbanCamoSkin_Kar98k.asr'],
 'lee_enfield': ['Misc\\Common.asr',
                 'DLCData\\DLC_Weapon_CamoRiflesSP_LeeEnfieldNo4.asr',
                 'DLCData\\DLC_Weapon_ColdWarfareWinterEP_SnowCamoSkin_LeeEnfieldNo4.asr',
                 'DLCData\\DLC_Weapon_NightFighterEP_NightCamoSkin_LeeEnfieldNo4.asr',
                 'DLCData\\DLC_Weapon_UrbanAssaultEP_UrbanCamoSkin_LeeEnfieldNo4.asr'],
 'm1_garand': ['Misc\\Common.asr', 'DLCData\\DLC_Weapon_AlliedForcesRP_M1Garand.asr'],
 'mannlicher': ['Misc\\Common.asr',
                'DLCData\\DLC_Weapon_CamoRiflesSP_Mannlicher.asr',
                'DLCData\\DLC_Weapon_ColdWarfareWinterEP_SnowCamoSkin_Mannlicher.asr',
                'DLCData\\DLC_Weapon_NightFighterEP_NightCamoSkin_Mannlicher.asr',
                'DLCData\\DLC_Weapon_UrbanAssaultEP_UrbanCamoSkin_Mannlicher.asr'],
 'mosin_nagant': ['Misc\\Common.asr',
                  'DLCData\\DLC_Weapon_CamoRiflesSP_MosinNagant.asr',
                  'DLCData\\DLC_Weapon_ColdWarfareWinterEP_SnowCamoSkin_MosinNagant.asr',
                  'DLCData\\DLC_Weapon_NightFighterEP_NightCamoSkin_MosinNagant.asr',
                  'DLCData\\DLC_Weapon_UrbanAssaultEP_UrbanCamoSkin_MosinNagant.asr'],
 'ross_mkiii': ['Misc\\Common.asr', 'DLCData\\DLC_Weapon_AlliedForcesRP_RossRifle.asr'],
 'springfield_m1903': ['Misc\\Common.asr',
                       'DLCData\\DLC_Weapon_CamoRiflesSP_Springfield.asr',
                       'DLCData\\DLC_Weapon_ColdWarfareWinterEP_SnowCamoSkin_Springfield.asr',
                       'DLCData\\DLC_Weapon_NightFighterEP_NightCamoSkin_Springfield.asr',
                       'DLCData\\DLC_Weapon_UrbanAssaultEP_UrbanCamoSkin_Springfield.asr'],
 'svt38': ['Misc\\Common.asr',
           'DLCData\\DLC_Weapon_LockAndLoadWP_SVT38.asr',
           'DLCData\\DLC_Weapon_NightFighterEP_Mauser.asr',
           'DLCData\\DLC_Weapon_NightFighterEP_NightCamoSkin_Mauser.asr'],
 'swedish_mauser': ['Misc\\Common.asr',
                    'DLCData\\DLC_Weapon_NightFighterEP_Mauser.asr',
                    'DLCData\\DLC_Weapon_NightFighterEP_NightCamoSkin_Mauser.asr'],
 'winchester_1895': ['Misc\\Common.asr',
                     'DLCData\\DLC_Weapon_UrbanAssaultEP_Winchester1895.asr',
                     'DLCData\\DLC_Weapon_UrbanAssaultEP_UrbanCamoSkin_Winchester1895.asr'],
 'zh-29': ['Misc\\Common.asr',
           'DLCData\\DLC_Weapon_ColdWarfareWinterEP_ZH-29.asr',
           'DLCData\\DLC_Weapon_ColdWarfareWinterEP_SnowCamoSkin_ZH-29.asr']}

# The M1 Carbine's scope is part of the rifle mesh itself: faces inside these boxes (model space, metres;
# x, y pointing DOWN, z along the barrel) are collapsed. 'boxes' test the face centre, 'any_boxes' any corner.
PART_SCOPES = {'m1_carbine': {'any_boxes': [(-0.04, 0.04, -0.2, -0.0725, -0.26, 0.1)],
                'archives': ['DLCData\\DLC_Weapon_AlliedForcesRP_M1Carbine.asr'],
                'boxes': [(-0.04, 0.04, -0.2, -0.0725, -0.26, 0.1),
                          (-0.045, 0.045, -0.2, -0.06, -0.04, 0.17),
                          (-0.02, 0.02, -0.2, -0.0605, -0.2, -0.1),
                          (-0.018, 0.018, -0.2, -0.0565, -0.036, 0.01),
                          (-0.025, 0.025, -0.2, -0.054, -0.165, -0.135)],
                'meshes': '^(l\\d#)?m1_carbine(_gold)?$'}}

RIFLES = {'carcano': ('Carcano', ['body', 'camo', 'snow', 'urban', 'night', 'gold']),
 'mosin_nagant': ('Mosin-Nagant', ['body', 'camo', 'snow', 'urban', 'night', 'gold']),
 'kar98k': ('Kar98k', ['body', 'camo', 'snow', 'urban', 'night', 'gold']),
 'springfield_m1903': ('Springfield', ['body', 'camo', 'snow', 'urban', 'night', 'gold']),
 'lee_enfield': ('Lee-Enfield', ['body', 'camo', 'snow', 'urban', 'night', 'gold']),
 'mannlicher': ('Mannlicher M1895', ['body', 'camo', 'snow', 'urban', 'night', 'gold']),
 'g43': ('Gewehr 43', ['body', 'camo', 'snow', 'urban', 'night', 'gold']),
 'swedish_mauser': ('Swedish Mauser', ['body', 'night', 'gold']),
 'winchester_1895': ('Winchester 1895', ['body', 'urban', 'gold']),
 'm1_garand': ('M1 Garand', ['body', 'gold']),
 'svt38': ('SVT-38', ['body', 'gold']),
 'ross_mkiii': ('Ross Mk III', ['body', 'gold']),
 'delisle_carbine': ('De Lisle', ['body', 'gold']),
 'zh-29': ('ZH-29', ['body', 'snow', 'gold']),
 'm1_carbine': ('M1 Carbine', ['body', 'gold'])}            # key: (menu name, [paints])
PAINTS = {'body': 'standard', 'camo': 'woodland camo', 'snow': 'winter', 'urban': 'urban',
          'night': 'night', 'gold': 'gold'}

GUI_ARCHIVE = r'GUIMenu\InGame_Common.gui'
COMMON = r'Misc\Common.asr'
HIDE_GROUPS = ('Shadow_BackPlate', 'Reticle_', 'Frame_FrontPlate')
KEEP = ('HitMarker', 'ring_shadow_3_Combined')
SIGHT_TEX = b'\\graphics\\menus\\scope\\scope_shadow_3.tga\0'
LENS_MASKS = [b'\\graphics\\hud\\scopes\\mask_fisheye_blurred.tga\0', b'\\graphics\\hud\\scopes\\scopedofalpha.tga\0']
BC7_ZERO = bytes([0x40]) + bytes(15)          # BC7 mode 6 block, RGBA 0


# --------------------------------------------------------------------------------------------- game folder
def find_game(arg=None):
    cands = []
    if arg:
        cands.append(arg)
    cfg = os.path.join(HERE, 'game_path.txt')
    if os.path.exists(cfg):
        cands.append(open(cfg, encoding='utf-8').read().strip().strip('"'))
    steam = []
    try:
        import winreg
        for hive, key in ((winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam'),
                          (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam')):
            try:
                with winreg.OpenKey(hive, key) as k:
                    for name in ('SteamPath', 'InstallPath'):
                        try:
                            steam.append(winreg.QueryValueEx(k, name)[0])
                        except OSError:
                            pass
            except OSError:
                pass
    except ImportError:
        pass
    steam += [r'C:\Program Files (x86)\Steam', r'C:\Program Files\Steam']
    libs = []
    for s in steam:
        vdf = os.path.join(s, 'steamapps', 'libraryfolders.vdf')
        libs.append(s)
        if os.path.exists(vdf):
            for m in re.finditer(r'"path"\s+"([^"]+)"', open(vdf, encoding='utf-8', errors='replace').read()):
                libs.append(m.group(1).replace('\\\\', '\\'))
    for lib in libs:
        cands.append(os.path.join(lib, 'steamapps', 'common', 'Sniper Elite 4'))
    for c in cands:
        if c and os.path.exists(os.path.join(c, COMMON)) and os.path.exists(os.path.join(c, GUI_ARCHIVE)):
            return os.path.normpath(c)
    raise SystemExit('Sniper Elite 4 not found. Run again with  --game "<path to the Sniper Elite 4 folder>"  '
                     'or put that path into game_path.txt next to IronSights.py.')


# --------------------------------------------------------------------------------------------- archives
def blocks_of(raw):
    """AsuraZbb: list of (compressed bytes, uncompressed size) per block."""
    tot, first = struct.unpack_from('<II', raw, 12)
    out = [(raw[24:24 + first], None)]
    p = 24 + first; got = len(zlib.decompress(out[0][0]))
    out[0] = (out[0][0], got)
    while got < tot:
        cs, us = struct.unpack_from('<II', raw, p)
        out.append((raw[p + 8:p + 8 + cs], us)); got += us; p += 8 + cs
    return out


def pack(header_tail, blocks):
    """Rebuild an AsuraZbb file: header = magic, total_size(=filesize-16), uncompressed, first block size,
    block size (header_tail = that last field from the original)."""
    body = blocks[0][0] + b''.join(struct.pack('<II', len(z), u) + z for z, u in blocks[1:])
    total = sum(u for _, u in blocks)
    return b'AsuraZbb' + struct.pack('<IIII', len(body) + 8, total, len(blocks[0][0]), header_tail) + body


def md5(b):
    return hashlib.md5(b).hexdigest()


def rscf_meshes(d, rx):
    """Render meshes = RSCF chunks of type 0: (name, payload offset, payload size)."""
    o = 8
    while o + 8 <= len(d):
        t = d[o:o + 4]; s = struct.unpack_from('<I', d, o + 4)[0]
        if s < 8 or o + s > len(d):
            break
        if t == b'RSCF' and struct.unpack_from('<I', d, o + 16)[0] == 0:
            size = struct.unpack_from('<I', d, o + 24)[0]
            e = d.index(b'\0', o + 28); name = bytes(d[o + 28:e]).decode('latin1')
            if rx.search(name):
                yield name, o + s - size, size
        o += s


def hide_scopes(d, rifle):
    n = 0
    rx = re.compile(r'^(l\d#)?%s(_[a-z0-9]+)?_scope' % re.escape(rifle), re.I)
    for name, p, size in list(rscf_meshes(d, rx)):
        count, nv, ni, nt = struct.unpack_from('<4I', d, p)
        idx = p + 44 + count * 24 + nv * 40
        assert ni == nt * 3 and idx + ni * 2 <= p + size, name
        d[idx:idx + ni * 2] = bytes(ni * 2)          # every triangle degenerate: nothing is drawn
        n += 1
    return n


def cut_part_scope(d, rifle):
    cfg = PART_SCOPES[rifle]; n = 0
    for name, p, size in list(rscf_meshes(d, re.compile(cfg['meshes'], re.I))):
        count, nv, ni, nt = struct.unpack_from('<4I', d, p)
        sx, sy, sz, ox, oy, oz = struct.unpack_from('<6f', d, p + 20 + count * 24)
        vb = p + 44 + count * 24; ib = vb + nv * 40
        pos = [(qx / 65536 * sx + ox, qy / 65536 * sy + oy, qz / 65536 * sz + oz)
               for qx, qy, qz in (struct.unpack_from('<3H', d, vb + v * 40) for v in range(nv))]
        for t in range(nt):
            a, b, c = struct.unpack_from('<3H', d, ib + t * 6)
            cx = (pos[a][0] + pos[b][0] + pos[c][0]) / 3
            cy = (pos[a][1] + pos[b][1] + pos[c][1]) / 3
            cz = (pos[a][2] + pos[b][2] + pos[c][2]) / 3
            hit = any(x0 < cx < x1 and y0 < cy < y1 and z0 < cz < z1 for x0, x1, y0, y1, z0, z1 in cfg['boxes'])
            hit = hit or any(x0 < pos[k][0] < x1 and y0 < pos[k][1] < y1 and z0 < pos[k][2] < z1
                             for k in (a, b, c) for x0, x1, y0, y1, z0, z1 in cfg.get('any_boxes', []))
            if hit:
                struct.pack_into('<3H', d, ib + t * 6, a, a, a); n += 1
    return n


def hide_scope_view(d):
    """HUD_SniperScope page: hide reticles, tube shadows and lens ring; keep one full-screen element whose
    texture becomes the open-sight picture."""
    i = d.find(b'HUD_SniperScope\0')
    while i >= 0 and d[i - 32:i - 28] != b'UIMP':
        i = d.find(b'HUD_SniperScope\0', i + 1)
    assert i > 0, 'HUD_SniperScope page not found'
    base = i - 32; end = base + struct.unpack_from('<I', d, base + 4)[0]
    group = None; n = 0
    for m in re.finditer(rb'([\x00-\xff]{4})\x21\x00\x00\x00([A-Za-z_][\x20-\x7e]*)\0', bytes(d[base:end])):
        typ = struct.unpack_from('<I', m.group(1))[0]
        if typ not in (1001, 2006):
            continue
        name = m.group(2).decode(); ns = base + m.start(2)
        pad = ns + ((len(name) + 1 + 3) // 4) * 4
        if typ == 2006:
            group = name; continue
        if name == 'ring_shadow_3_Combined':
            struct.pack_into('<4f', d, pad, 1.0, 1.0, 1.0, 1.0)
            continue
        if group and group.startswith(HIDE_GROUPS) and name not in KEEP:
            x0, x1, y0, y1 = struct.unpack_from('<4f', d, pad + 16)
            struct.pack_into('<f', d, pad + 12, 0.0)
            struct.pack_into('<4f', d, pad + 16, x0, x0, y0, y0)
            n += 1
    return n


def put_sight(d, rifle, paint):
    data = lzma.decompress(open(os.path.join(SIGHTS, '%s_%s.bc7.xz' % (rifle, paint)), 'rb').read())
    i = d.find(SIGHT_TEX); o = i - 28
    assert i > 0 and d[o:o + 4] == b'RSCF', 'scope picture texture not found'
    s = struct.unpack_from('<I', d, o + 4)[0]; dd = d.find(b'DDS ', o, o + 300)
    assert struct.unpack_from('<II', d, dd + 12) == (2048, 2048) and struct.unpack_from('<I', d, dd + 128)[0] == 98
    start = dd + 148
    assert start + len(data) == o + s, 'scope picture size differs (other game version?)'
    d[start:start + len(data)] = data


def blank_lens(d):
    n = 0
    for key in LENS_MASKS:
        i = d.find(key)
        assert i > 0 and d[i - 28:i - 24] == b'RSCF', key
        o = i - 28; s = struct.unpack_from('<I', d, o + 4)[0]
        dd = d.find(b'DDS ', o, o + 200)
        h, w = struct.unpack_from('<II', d, dd + 12); mips = struct.unpack_from('<I', d, dd + 28)[0]
        assert d[dd + 84:dd + 88] == b'DX10' and struct.unpack_from('<I', d, dd + 128)[0] in (98, 99)
        size = 0
        for _ in range(max(1, mips)):
            size += max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * 16; w, h = max(1, w // 2), max(1, h // 2)
        start = dd + 148
        assert start + size <= o + s
        d[start:start + size] = BC7_ZERO * (size // 16)
        n += 1
    return n


# --------------------------------------------------------------------------------------------- install
def archives():
    out = [GUI_ARCHIVE]
    for rel in [a for v in SCOPE_ARCHIVES.values() for a in v] + [a for v in PART_SCOPES.values() for a in v['archives']]:
        if rel not in out:
            out.append(rel)
    return out


def state_path(game):
    return os.path.join(game, BACKUP_DIR, 'state.json')


def load_state(game):
    try:
        return json.load(open(state_path(game), encoding='utf-8'))
    except (OSError, ValueError):
        return None


def save_state(game, st):
    tmp = state_path(game) + '.tmp'
    json.dump(st, open(tmp, 'w', encoding='utf-8'), indent=1)
    os.replace(tmp, state_path(game))


def patch_archive(rel, d, rifle, paint):
    msgs = []
    for r, rels in SCOPE_ARCHIVES.items():
        if rel in rels:
            n = hide_scopes(d, r)
            if n:
                msgs.append('%s scope: %d models' % (r, n))
    for r, cfg in PART_SCOPES.items():
        if rel in cfg['archives']:
            msgs.append('%s scope: %d faces' % (r, cut_part_scope(d, r)))
    if rel == GUI_ARCHIVE:
        msgs.append('scope view: %d elements hidden' % hide_scope_view(d))
        put_sight(d, rifle, paint); msgs.append('sight picture: %s %s' % (rifle, paint))
    if rel == COMMON:
        msgs.append('lens effect masks: %d' % blank_lens(d))
    return msgs


def install(game, rifle, paint):
    if rifle not in RIFLES or paint not in RIFLES[rifle][1]:
        raise SystemExit('unknown rifle/paint: %s %s' % (rifle, paint))
    if load_state(game):
        print('Removing the previous installation first...')
        uninstall(game, quiet=True)
    bdir = os.path.join(game, BACKUP_DIR); os.makedirs(bdir, exist_ok=True)
    st = {'version': VERSION, 'rifle': rifle, 'paint': paint, 'files': {}}
    rels = archives()
    for k, rel in enumerate(rels, 1):
        path = os.path.join(game, rel)
        if not os.path.exists(path):
            print('[%d/%d] %s - not present, skipped' % (k, len(rels), rel)); continue
        raw = open(path, 'rb').read()
        if raw[:8] != b'AsuraZbb':
            print('[%d/%d] %s - unexpected format, skipped' % (k, len(rels), rel)); continue
        blocks = blocks_of(raw)
        d = bytearray(b''.join(zlib.decompress(z) for z, _ in blocks))
        msgs = patch_archive(rel, d, rifle, paint)
        new_blocks = []; saved = {}; off = 0
        safe = re.sub(r'[\\/:]', '_', rel)
        for i, (z, us) in enumerate(blocks):
            n = bytes(d[off:off + us]); off += us
            if n != zlib.decompress(z):
                c = zlib.compressobj(9, zlib.DEFLATED, 12, 9, zlib.Z_FIXED)
                bname = '%s.block%d' % (safe, i)
                open(os.path.join(bdir, bname), 'wb').write(z)
                saved[str(i)] = bname
                z = c.compress(n) + c.flush()
            new_blocks.append((z, us))
        if not saved:
            print('[%d/%d] %s - nothing to change' % (k, len(rels), rel)); continue
        out = pack(struct.unpack_from('<I', raw, 20)[0], new_blocks)
        assert b''.join(zlib.decompress(z) for z, _ in blocks_of(out)) == bytes(d)
        st['files'][rel] = {'orig_md5': md5(raw), 'orig_header': raw[:24].hex(), 'blocks': saved,
                            'patched_md5': md5(out)}
        save_state(game, st)                      # backup is recorded before the file is replaced
        open(path + '.tmp', 'wb').write(out); os.replace(path + '.tmp', path)
        print('[%d/%d] %s - %s' % (k, len(rels), rel, '; '.join(msgs)))
    print('\nInstalled: open sights for %s (%s paint).' % (RIFLES[rifle][0], PAINTS[paint]))


def uninstall(game, quiet=False):
    st = load_state(game)
    if not st:
        if not quiet:
            print('Iron Sights is not installed in', game)
        return
    bdir = os.path.join(game, BACKUP_DIR); left = {}
    for rel, info in st['files'].items():
        path = os.path.join(game, rel)
        raw = open(path, 'rb').read()
        if md5(raw) == info['orig_md5']:
            continue
        if md5(raw) != info['patched_md5']:
            print('%s changed since install (game update or Steam file check?) - left as it is' % rel)
            continue
        blocks = blocks_of(raw)
        for i, bname in info['blocks'].items():
            blocks[int(i)] = (open(os.path.join(bdir, bname), 'rb').read(), blocks[int(i)][1])
        head = bytes.fromhex(info['orig_header'])
        out = pack(struct.unpack_from('<I', head, 20)[0], blocks)
        if md5(out) != info['orig_md5']:
            print('%s - restore check failed, left as it is (use Steam "Verify integrity of game files")' % rel)
            left[rel] = info; continue
        open(path + '.tmp', 'wb').write(out); os.replace(path + '.tmp', path)
        if not quiet:
            print('%s restored' % rel)
    if left:
        st['files'] = left; save_state(game, st)
        return
    for f in os.listdir(bdir):
        os.remove(os.path.join(bdir, f))
    os.rmdir(bdir)
    if not quiet:
        print('\nUninstalled: scopes are back.')


# --------------------------------------------------------------------------------------------- menu
def ask(n, prompt='Number + Enter: '):
    while True:
        a = input(prompt).strip()
        if a.isdigit() and 1 <= int(a) <= n:
            return int(a)
        print('Type a number from 1 to %d.' % n)


def choose():
    keys = list(RIFLES)
    print('\nWhich rifle will you play with?')
    for k, r in enumerate(keys, 1):
        print('  %2d - %s' % (k, RIFLES[r][0]))
    rifle = keys[ask(len(keys)) - 1]
    paints = RIFLES[rifle][1]
    if len(paints) == 1:
        return rifle, paints[0]
    print('\nWhich paint of the %s?' % RIFLES[rifle][0])
    for k, p in enumerate(paints, 1):
        print('  %d - %s' % (k, PAINTS[p]))
    return rifle, paints[ask(len(paints)) - 1]


def main():
    args = sys.argv[1:]; game_arg = None
    if '--game' in args:
        i = args.index('--game'); game_arg = args[i + 1]; del args[i:i + 2]
    game = find_game(game_arg)
    print('Iron Sights %s   game: %s' % (VERSION, game))
    cmd = args[0] if args else None
    if cmd == 'install':
        install(game, args[1], args[2])
    elif cmd == 'uninstall':
        uninstall(game)
    elif cmd == 'status':
        st = load_state(game)
        print('installed: %s %s' % (st['rifle'], st['paint']) if st else 'not installed')
    else:
        st = load_state(game)
        print('Now: ' + ('open sights for %s (%s)' % (RIFLES[st['rifle']][0], PAINTS[st['paint']]) if st
                         else 'not installed (normal scopes)'))
        print('\n  1 - install / change rifle\n  2 - uninstall (scopes back)\n  3 - quit')
        a = ask(3)
        if a == 1:
            install(game, *choose())
        elif a == 2:
            uninstall(game)


if __name__ == '__main__':
    code = 0
    try:
        main()
    except AssertionError as e:
        print('Stopped: unexpected game data (%s). Nothing more was changed.' % e); code = 1
    except SystemExit as e:
        if e.code not in (None, 0):
            print(e.code); code = 1
    except (KeyboardInterrupt, EOFError):
        code = 1
    if FROZEN and len(sys.argv) == 1:               # double-clicked: keep the window open
        print()
        try:
            input('Press Enter to close.')
        except (KeyboardInterrupt, EOFError):
            pass
    sys.exit(code)
