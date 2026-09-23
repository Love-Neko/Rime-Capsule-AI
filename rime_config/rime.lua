--[[
  rime.lua - Rime Lua 插件注册入口
  适用于 Windows 小狼毫 (Weasel) / macOS 鼠须管 (Squirrel) / Linux fcitx5-rime
--]]

local ok, jf = pcall(require, "jev_filter")
if not ok then
    local ok2, jf2 = pcall(require, "lua/jev_filter")
    if ok2 then
        jf = jf2
    end
end

-- 重要：librime-lua 要求 lua_filter 必须绑定到一个 function，不能直接是 table
if type(jf) == "table" and (jf.func or jf.filter) then
    local filter_func = jf.func or jf.filter
    jev_filter = function(input, env)
        return filter_func(input, env)
    end
elseif type(jf) == "function" then
    jev_filter = jf
else
    -- 兜底直通函数，保证无论如何候选词绝不消失
    jev_filter = function(input, env)
        for cand in input:iter() do
            yield(cand)
        end
    end
end
