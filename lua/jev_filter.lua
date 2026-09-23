--[[
  Jev (TypeSafe AI) 候选词语义重排过滤器 (方案 A - Tab 键智能召唤)
  适用于 Rime 输入法引擎（Windows 小狼毫 Weasel / macOS 鼠须管 Squirrel）
  特点：零黑窗口、零子进程、打字零卡顿、绝对防黑屏
--]]

local M = {}

local req_file = (os.getenv("TEMP") or "/tmp") .. "/rime_jev_req.txt"
local res_file = (os.getenv("TEMP") or "/tmp") .. "/rime_jev_res.txt"

-- 获取用户光标前的上下文文本（来自上屏历史）
local function get_context_text(env)
    local ctx = env.engine.context
    if not ctx then return "" end

    local text = ""
    local history = ctx.commit_history
    if history then
        if history.latest_text then
            local t = history:latest_text()
            if t and #t > 0 then
                text = t
            end
        end
        if #text == 0 and history.iter then
            local parts = {}
            for record in history:iter() do
                if record and record.text and #record.text > 0 then
                    table.insert(parts, record.text)
                end
            end
            if #parts > 0 then
                local start_idx = math.max(1, #parts - 2)
                local sub = {}
                for i = start_idx, #parts do
                    table.insert(sub, parts[i])
                end
                text = table.concat(sub, "")
            end
        end
    end
    return text
end

function M.init(env)
end

function M.func(input, env)
    local ctx = env.engine.context
    local pinyin = (ctx and ctx.input) or ""

    -- 1. 安全读取前 20 个候选词
    local cands = {}
    for cand in input:iter() do
        table.insert(cands, cand)
        if #cands >= 20 then
            break
        end
    end

    if #cands == 0 then
        return
    end

    -- 2. 常规打字期间：后台悄悄通过纯 C fopen 写入请求文件（<0.05ms，0进程，绝不卡死）
    -- 这样 Python 桥接层在后台即可提前完成 Jev AI 预测，按下 Tab 键时立等可取！
    if #pinyin >= 2 then
        local cand_texts = {}
        for i = 1, math.min(#cands, 6) do
            table.insert(cand_texts, cands[i].text)
        end
        local context_text = get_context_text(env)
        local f = io.open(req_file, "w")
        if f then
            f:write(context_text .. "\n" .. pinyin .. "\n" .. table.concat(cand_texts, ",") .. "\n")
            f:close()
        end
    end

    -- 3. 判断是否按下了 Tab 键（方案 A：按键召唤）
    local is_tab_triggered = ctx and ctx:get_option("jev_ai")

    -- 如果没有按 Tab 键，原样极速输出候选词，完全不耗额外算力，打字飞快
    if not is_tab_triggered then
        for _, cand in ipairs(cands) do
            yield(cand)
        end
        for cand in input:iter() do
            yield(cand)
        end
        return
    end

    -- 4. 用户按下了 Tab 键！读取预计算好的 AI 决策结果
    local chosen_text = nil
    local tag = "✦ Jev"

    -- 等待获取结果文件（如果后台已预计算好，则耗时 < 1毫秒；若未就绪，最多等待 1.2 秒）
    local start_t = os.clock()
    while (os.clock() - start_t) < 1.20 do
        local rf = io.open(res_file, "r")
        if rf then
            local content = rf:read("*a")
            rf:close()
            if content and #content > 0 then
                local res_pinyin = content:match("pinyin=([^\n\r]+)")
                local res_selected = content:match("selected=([^\n\r]+)")
                local res_tag = content:match("tag=([^\n\r]+)")
                -- 清除空格和分音符做宽容匹配
                local p1 = pinyin:gsub("[%s']+", "")
                local p2 = (res_pinyin or ""):gsub("[%s']+", "")
                if p1 == p2 and res_selected and #res_selected > 0 then
                    chosen_text = res_selected
                    if res_tag and #res_tag > 0 then tag = res_tag end
                    break
                end
            end
        end
        -- 微休 8ms
        local t0 = os.clock()
        while (os.clock() - t0) < 0.008 do end
    end

    -- 复位开关，确保下次打字默认回归常规输入
    ctx:set_option("jev_ai", false)

    -- 5. 如果获取到 AI 最佳候选，打上 ✦ Jev 并排至第 1 位
    if chosen_text then
        local chosen_cand = nil
        for _, cand in ipairs(cands) do
            if cand.text == chosen_text then
                chosen_cand = cand
                break
            end
        end

        if chosen_cand then
            if chosen_cand.get_genuine then
                chosen_cand:get_genuine().comment = tag
            else
                chosen_cand.comment = tag
            end

            -- 首选推送 Jev 词
            yield(chosen_cand)

            -- 输出其余候选词
            for _, cand in ipairs(cands) do
                if cand ~= chosen_cand then
                    yield(cand)
                end
            end
            for cand in input:iter() do
                if cand.text ~= chosen_text then
                    yield(cand)
                end
            end
            return
        end
    end

    -- 超时或未匹配：平滑回退，原样输出
    for _, cand in ipairs(cands) do
        yield(cand)
    end
    for cand in input:iter() do
        yield(cand)
    end
end

M.filter = M.func

return M
