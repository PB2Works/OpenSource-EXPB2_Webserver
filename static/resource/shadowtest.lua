-- Draw line from eyes to end point
-- to draw, i need initial region and final region
-- 

local i = 0
local increment = 0.1
local originX = 0
local originY = 0
local radius = 700

local CLEAR_DRAW_OPCODE = 580
local SET_LINESTYLE_OPCODE = 581
local SET_DRAWSTART_OPCODE = 582
local DRAW_TO_OPCODE = 583
local REGION_TO_CHAR_OPCODE = 80
local BRUSH_THICKNESS = 20

local startRegion = getRegionFromUID("#start")
local endRegion = getRegionFromUID("#end")
local localPlayer = getLocalPlayer()

local frameCount = 0

function main()
    -- Clear drawing every 3 frames
    -- Clear drawing before drawing them so drawing does not stutter
    frameCount = frameCount + 1
    if frameCount == 2 then
        exec(CLEAR_DRAW_OPCODE, "", "")
        frameCount = 0
    end
    
    for angle = 0, 6.283, 0.025 do
        local x = math.sin(angle)
        local y = math.cos(angle)
        
        -- Position start region to player
        exec(REGION_TO_CHAR_OPCODE, tostring(startRegion.id), tostring(localPlayer.id))
        
        originX = startRegion.x
        originY = startRegion.y - 50
        
        -- Position end region to end of circle
        endRegion.x = originX + x * radius
        endRegion.y = originY + y * radius
            
        -- Slowly move vision region away from player in the direction of angle, stopping if unable to trace region from vision to start OR reaching end of circle
        for offset = 0, radius, 25 do
            -- if we can trace from start to end, don't bother moving vision
            if traceable(originX, originY, endRegion.x, endRegion.y) then
                break
            end
            
            local visionX = originX + offset * x
            local visionY = originY + offset * y
           
            if not traceable(visionX, visionY, originX, originY) then
                startRegion.x = visionX + x * BRUSH_THICKNESS -- offset a litle due to thickness of brush
                startRegion.y = visionY + y * BRUSH_THICKNESS
                
                
                -- Draw from start region to end region
                exec(SET_LINESTYLE_OPCODE, tostring(BRUSH_THICKNESS), "000000")
                exec(SET_DRAWSTART_OPCODE, tostring(startRegion.id), "")
                exec(DRAW_TO_OPCODE, tostring(endRegion.id), "")
                break
            end
        end
        
    end
    
end


frameRegister(main)