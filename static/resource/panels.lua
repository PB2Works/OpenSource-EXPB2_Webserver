local SCANCODE_I         = 73
local SCANCODE_J         = 74
local SCANCODE_K         = 75
local SCANCODE_L         = 76
local SCANCODE_O         = 79
local SCANCODE_R         = 82
local SCANCODE_T         = 84
local SCANCODE_F         = 70
local SCANCODE_G         = 71
local SCANCODE_H         = 72
local SCANCODE_BACKSLASH = 220

local startTime = timeMS()
local playTime = 800 -- How long the animation should take (in milliseconds)
local hintStage = 0

local Pixel_panel = {}
local palette = 1
local Colors = {{"#000000", "#FFFFFF"}}
Colors[2] = {"#FF0000", "#0000AA"}
Colors[3] = {"#0000FF", "#FFFF00"}
local PALETTES_TOTAL = #Colors

local SCREEN_X = 150
local SCREEN_Y = -240
local SCREEN_W = 16
local SCREEN_H = 9
local PSIZE = 20

for n = 1, 16 do
 Pixel_panel[n] = {}
 for j = 1, 9 do
  Pixel_panel[n][j] = getMovableFromUID("#door*" .. j .. '*' .. n)
  print("#door*" .. n .. '*' .. j)
 end
end

local Frames = {}
Frames[1] = {
 {0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}
}

Frames[2] = {
 {0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}
}

Frames[3] = {
 {0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0},
 {0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0},
 {1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0}
}

Frames[4] = {
 {0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0},
 {0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0},
 {0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0},
 {0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0},
 {0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0},
 {0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0},
 {1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0}
}

Frames[5] = {
 {0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0},
 {1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0},
 {0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0},
 {0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0},
 {0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0},
 {0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0},
 {1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0},
 {0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0},
 {0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}
}

Frames[6] = {
 {0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
 {0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}
}

local TOTAL_FRAMES = #Frames

local flip_colors = 1
local function SetFrame(index)
 for y = 1, 9 do
  if (Frames[index][y] == nil) then break end
  for x = 1, 16 do 
   local color = Frames[index][y][x]
   if (color == nil) then break end
   color = (flip_colors + color) % 2
   Pixel_panel[x][y].color = Colors[palette][color + 1]
  end
 end
end

local function handleFrame(dst)
 local point = dst / playTime
 point = point - math.floor(point)
 local frame = math.floor((point * TOTAL_FRAMES)) + 1
 SetFrame(frame)
end

local function handleHints(dst)
 if hintStage == 0 and dst > 1500 then
  setHint("Press F to flip colors")
  hintStage = 1
 end
 if hintStage == 1 and dst > 4000 then
  setHint("Press R to flip palettes")
  hintStage = 2
 end
 if hintStage == 2 and dst > 6000 then
  setHint("Use J and K to switch change speed")
  hintStage = 3
 end
 if hintStage == 3 and dst > 8000 then
  setHint("")
  hintStage = 4
 end
end

local function handleScreen(dst)
 for x=1, SCREEN_W do
  for y=1, SCREEN_H do
   local ox = SCREEN_X + PSIZE * x
   local oy = SCREEN_Y + PSIZE * y
   local nx = ox
   local ny = oy + 40 * math.sin(x * 50 + dst / 300)
   Pixel_panel[x][y].x = nx
   Pixel_panel[x][y].y = ny
  end
 end
end

keyDownRegister(function(keyCode)
 if keyCode == SCANCODE_F then
  flip_colors = 1 - flip_colors
  print("Colors are now " .. ({"flipped", "normal"})[flip_colors + 1])
 end
 if keyCode == SCANCODE_J then
  playTime = playTime * 1.1
 end
 if keyCode == SCANCODE_K then
  playTime = playTime * 0.9
 end
 if keyCode == SCANCODE_K or keyCode == SCANCODE_J then
  local ttp = math.floor((playTime / 1000) * 100) / 100
  print("Animation time: &2 " .. ttp .. "&0 seconds")
 end
 if keyCode == SCANCODE_R then
  palette = (palette % PALETTES_TOTAL) + 1
  print("Palette #" .. palette)
 end
end)

frameRegister(function()
 local dst = timeMS() - startTime
 handleFrame(dst)
 handleHints(dst)
 handleScreen(dst)
end)