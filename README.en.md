# Mortar Aid For PUBG

Minimal mortar assistant tool for PUBG.

中文说明: [README.md](README.md)

## Disclaimer

For technical communication and entertainment purposes only.

## Core Idea

1. Use a 100m map grid as scale calibration.
2. Apply elevation-angle correction.

We combine projectile motion with geometric elevation relation:

```math

y = - \frac{g}{2v_0^2 \cos^2{\theta}} x^2 + x\tan{\theta}

```

```math

\tan{\beta} = \frac{H}{L}

```

Here, $\theta$ is mortar elevation, $v_0$ is muzzle velocity, and $g$ is gravity.

The target value is $R$ (the mortar setting this tool outputs).

![image](img/image.png)

For uphill shots, elevation $\beta$ is included.

In PUBG, max mortar range 700m is approximately 45°.

(Observed in-game, not strictly measured)

121m shot has a larger elevation:

![image](img/121m.png)

700m shot is around 45°, matching projectile behavior:

![image](img/700m.png)

With $\theta = 45°$:

```math

R = \frac{v_0^2\sin{2\theta}}{g} = \frac{v_0^2}{g}

```

$R$ here is theoretical max horizontal range on level ground.

For target $(L, H)$, substituting into projectile equation yields:

```math

\tan{\theta} = \frac{H}{L - \frac{L^2}{R}}

```

And then:

```math
R = \frac{\frac{HLv_0^2}{g} + L^3 \pm \sqrt{(\frac{HLv_0^2}{g}  + L^3)^2 - (H^2 + L^2)(L^4 + \frac{2HLv_0^2}{g})}}{H^2 + L^2}
```

Using $\tan{\beta} = \frac{H}{L}$ and $M = \frac{v_0^2}{g}$ (set as 700m in practice), we get:

```math
R = \frac{L + tan{\beta}(M - \sqrt{M^2 - 2LM\tan{\beta} - L^2})}{\tan^2{\beta} + 1}
```

So the implementation becomes:

- Compute $L$ from scale points.
- Compute $\beta$ from screen-space elevation.
- Solve for mortar setting $R$.

## Build

```bash
python.exe -m PyInstaller --clean --noconfirm MortarAid.spec
```

If you use project venv:

```bash
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm MortarAid.spec
```

Or download from release.

## Release

1. Build onedir output:

```bash
python.exe -m PyInstaller --clean --noconfirm MortarAid.spec
```

2. Compress for distribution:

```powershell
Compress-Archive -Path .\dist\MortarAid\* -DestinationPath .\dist\MortarAid-win64.zip -Force
```

---

Alt + Q: Start measurement

Alt + Left: Set point

Alt + Right: Reset workflow

R: One-key set mortar scale after calculation

Settings entry: Menu -> Settings

Configurable options:

- Language (Chinese/English)
- Alt + Q trigger window (0.3 / 0.5 / 0.8s)

>If hotkeys do not trigger, right-click the app icon -> Properties -> enable "Run this program as an administrator".

*** (Step 1-2: open map and keep zoom unchanged during these two steps) ***
**1:** Mark two points for one 100m grid distance. Tool calibrates the scale.
![step1](img/guide-step1.png)

**2:** Mark your position and target position.
![step2](img/guide-step2.png)

*** (Step 3: do this while seated on the mortar) ***
**3:** Mark target icon position on screen (after pressing TAB/ESC to show cursor). Tool computes elevation.

Then the tool outputs mortar range. Press R to auto-set mortar scale.

## Developer Workflow

### 0) Structure

- main.py: app composition layer, page switching, workflow orchestration, event wiring.
- mortar_tools/calculator.py: distance, elevation, and final mortar range calculation.
- mortar_tools/hotkey_state.py: Alt/Q state machine (start/exit anti-misfire logic).
- mortar_tools/settings_store.py: settings read/write and path resolution.
- mortar_tools/i18n_texts.py: centralized Chinese/English UI strings.

### 1) Start Flow (Alt + Q)

- Record Alt/Q press timestamps.
- Start only when interval <= start_combo_max_interval.
- Supports either Alt-first or Q-first.

### 2) Exit During Flow (Alt + Q)

- First 1.5s after start is anti-misfire window.
- Inside this window:
  - one Alt+Q: exit after window ends.
  - multiple Alt+Q: treated as misfire, no exit.
- After 1.5s, Alt+Q exits immediately.

### 3) Reset During Flow (Alt + Right)

- Sets reset_requested = True.
- Current step stops and restarts from scale step 1.

### 4) Mark Points (Alt + Left)

- Records mouse coordinates.
- Collects scale points, distance points, and elevation point.

### 5) Quick Adjust in Result Window (R)

- Result window stays for 5 seconds.
- Press R only within this 5-second window to auto-scroll.
- Auto-scroll resets to 700 first, then scrolls to target scale.

### 6) Settings Persistence

- Single-window app with Home/Settings switch.
- Settings page supports language and trigger window.
- On Windows, saved to %APPDATA%/MortarAid/settings.json.
- Falls back to legacy root settings.json if needed.

## References

> [1] 绝地King-of-Mortar. PUBG mortar formula derivation, XiaoHeihe, 2025-01-03.
> https://api.xiaoheihe.cn/v3/bbs/app/api/web/share?link_id=b7a56f9c397c
>
> [2] 一只黄小娥. Bilibili, 2024-10-03.
> https://www.bilibili.com/video/BV1Ub4VeyEFA/?vd_source=56c580e6d408a69243bf3cc1af31f92d
>
> [3] 一只黄小娥. Mortar range tool (manual version) history, 2025/12/6.
> https://www.yzhxe.cn/file-downloads/1/4
