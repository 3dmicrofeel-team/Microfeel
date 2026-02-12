Encounter Gameplay Knowledge Base（Atomic Action Modules | RAG Chunk Format）
0. 通用数据结构约定（Common Data Types）

FVector：{X=0,Y=0,Z=0}

FRotator：{Pitch=0,Yaw=0,Roll=0}

Actor：从 World.GetByID() 或 Spawn API 获取的对象

Actor[]：Lua 数组（1 开始）

TMap：Lua table 字典

A. World 模块（核心玩法 API）
A1. 获取对象（Player / NPC）

World.GetByID(uid) -> Actor|nil
说明：通过 ID 获取 Actor，例如 Player 或 Tag_A NPC。
参数：

uid：string，例如 "Player"、"Tag_A"、"Tag_B"

示例：

local player = World.GetByID("Player")
local npcA = World.GetByID("Tag_A")


推荐用法：

local player = World.GetByID("Player")
if not player or not player:IsValid() then return end


常见错误：

未判空就调用 player:GetPos()

A2. 延迟 / 节奏控制（Wait）

World.Wait(seconds) -> nil（异步）
说明：暂停脚本执行若干秒，用于节奏控制。
参数：

seconds：number

示例：

World.Wait(0.8)


推荐用法：

npcA:MoveTo(locA)
World.Wait(1.0)
npcA:LookAt(player)


常见错误：

对话/动作之间没有 Wait，导致剧情刷屏

A3. 播放特效（FX）

World.PlayFX(id, loc) -> nil
说明：在指定位置播放特效。
参数：

id：string，FX 资源 ID

loc：FVector

示例：

World.PlayFX("FX_Explosion", {X=0, Y=0, Z=0})


推荐用法：

World.PlayFX("FX_Explosion", base)
World.Wait(0.3)


常见错误：

loc 传入 nil

A4. 播放 3D 音效

World.PlaySound(id, loc) -> nil
说明：在世界坐标播放 3D 音效。
参数：

id：string

loc：FVector

示例：

World.PlaySound("SFX_Hit", {X=0, Y=0, Z=0})


推荐用法：

World.PlaySound("SFX_Hit", base)
World.Wait(0.2)

A5. 播放 2D 音乐

World.PlaySound2D(id) -> AudioObject|nil
说明：播放 2D 音频（通常是 BGM），返回音频对象用于停止。
参数：

id：string

示例：

local audio = World.PlaySound2D("BGM_1")


推荐用法：

local bgm = World.PlaySound2D("BGM_1")
World.Wait(5.0)
World.StopSound(bgm)


常见错误：

没保存 audioObj，导致无法停止

A6. 停止 2D 音频

World.StopSound(audioObj) -> nil
说明：停止由 PlaySound2D 返回的音频对象。
参数：

audioObj：AudioObject

示例：

World.StopSound(audio)

A7. 生成敌人（SpawnEnemy）

World.SpawnEnemy(id, loc, count) -> Actor[]
说明：在指定位置生成敌人。
参数：

id：string（例如 "Spider_Minion_1"）

loc：FVector

count：int

示例：

local es = World.SpawnEnemy("Spider_Minion_1", {X=300, Y=0, Z=0}, 3)


推荐用法：

World.PlaySound("SFX_Hit", base)
World.PlayFX("FX_Explosion", base)
World.SpawnEnemy("Spider_Minion_1", {X=base.X + 150, Y=base.Y, Z=base.Z}, 2)
UI.Toast("敌人出现！")


常见错误：

count 写成 0

A8. 在玩家周围生成敌人

World.SpawnEnemyAtPlayer(id, count) -> Actor[]
说明：在玩家附近生成敌人（自动定位）。
参数：

id：string

count：int

示例：

local es = World.SpawnEnemyAtPlayer("Spider_Minion_1", 2)

A9. 销毁对象（Destroy Actor）

World.Destroy(obj) -> nil
说明：销毁一个 Actor。
参数：

obj：Actor

示例：

World.Destroy(npcA)

A10. 根据 ID 销毁对象

World.DestroyByID(uid) -> nil
说明：通过 ID 销毁对象。
参数：

uid：string

示例：

World.DestroyByID("enc01_smith")

B. UI 模块（交互核心）
B1. Toast（提示文本）

UI.Toast(text) -> nil（异步）
说明：屏幕弹出提示文本。
参数：

text：string

示例：

UI.Toast("任务开始")


推荐用法：

UI.Toast("你获得了 Money x10")
World.Wait(0.5)

B2. FadeOut

UI.FadeOut(duration) -> nil（异步）
说明：画面淡出。
参数：

duration：number

示例：

UI.FadeOut(0.5)

B3. FadeIn

UI.FadeIn(duration) -> nil（异步）
说明：画面淡入。
参数：

duration：number

示例：

UI.FadeIn(0.5)

B4. 显示对白（ShowDialogue）

UI.ShowDialogue(name, text) -> nil|any（异步）
说明：显示 UI 对话框。**重要：玩家说话必须使用此函数，不能使用ApproachAndSay**。
参数：

name：string（说话者名称，玩家说话时使用"Player"或角色名）

text：string（对话内容，直接使用引号包裹，不要使用方括号）

示例：

UI.ShowDialogue("商人", "你看起来不像本地人。")
UI.ShowDialogue("Player", "是的，我来自远方。")  // 玩家说话


推荐用法：

UI.ShowDialogue("旅人", "等等！你能帮我一下吗？")
World.Wait(0.6)
UI.ShowDialogue("Player", "当然可以，需要什么帮助？")  // 玩家说话
World.Wait(0.6)


常见错误：

连续多句对白无 Wait
玩家说话使用了ApproachAndSay（错误！玩家必须用UI.ShowDialogue）
对话内容使用了方括号（错误：`"[文本]"`，正确：`"文本"`）

B5. 二选一选择（Ask）

UI.Ask(msg, btnA, btnB) -> bool|string|any（异步）
说明：弹出二选一对话框。返回值依赖蓝图实现，常见为 bool。
参数：

msg：string

btnA：string

btnB：string

示例：

local ok = UI.Ask("你愿意帮忙吗？", "帮", "不帮")


推荐用法：

local ok = UI.Ask("你要插手吗？", "插手", "离开")
if ok == true then
    UI.Toast("你决定介入。")
else
    UI.Toast("你决定远离麻烦。")
end

B6. 多选项选择（AskMany）

UI.AskMany(title, options) -> any（异步）
说明：弹出多选项列表。返回值通常为数字索引（1 开始）。
参数：

title：string

options：string[]

示例：

local r = UI.AskMany("你打算怎么做？", {"介入", "旁观", "离开"})


推荐用法：

local r = UI.AskMany("你打算怎么做？", {"帮他作证", "揭穿他", "不说话"})
if r == 1 then
elseif r == 2 then
else
end


常见错误：

用 r==0 判断（Lua 数组从 1 开始）

B7. 触发小游戏

UI.PlayMiniGame(gameType, lv) -> string|any（异步）
说明：启动小游戏。返回值依赖蓝图。
参数：

gameType：string（例如 "TTT"）

lv：int

示例：

local r = UI.PlayMiniGame("TTT", 2)

C. System 模块（脚本控制）
C1. Exit（退出当前脚本）

System.Exit() -> nil
说明：退出当前 Encounter 脚本。
参数：无

示例：

System.Exit()


推荐用法：

World.Wait(0.8)
System.Exit()


常见错误：

忘记 Exit 导致脚本不结束

C2. ExitAll

System.ExitAll() -> nil
说明：退出全部脚本。一般不建议 Encounter 使用。
参数：无

示例：

System.ExitAll()

D. Entity 通用接口（Actor 基础能力）
D1. IsValid

obj:IsValid() -> bool
说明：判断 Actor 是否有效。
参数：无

示例：

if npcA and npcA:IsValid() then
end

D2. GetPos

obj:GetPos() -> FVector
说明：获取 Actor 世界坐标。
参数：无

示例：

local ppos = player:GetPos()

D3. GetRot

obj:GetRot() -> FRotator
说明：获取 Actor 世界旋转。
参数：无

示例：

local rot = npcA:GetRot()

D4. Teleport

obj:Teleport(loc, rot) -> nil
说明：瞬移 Actor 到指定位置和旋转。
参数：

loc：FVector

rot：FRotator

示例：

npcA:Teleport({X=0,Y=0,Z=0},{Pitch=0,Yaw=90,Roll=0})

D5. Destroy（对象自毁）

obj:Destroy() -> nil
说明：Actor 自毁。
参数：无

示例：

npcA:Destroy()

D6. AddTrigger（给 Actor 添加触发器）

obj:AddTrigger(type, range, code, once) -> nil
说明：给 Actor 添加触发器事件。
参数：

type：string

range：number

code：string

once：bool

示例：

npcA:AddTrigger("Enter", 300, "UI.Toast('trigger')", true)

E. Performer（NPC 行为接口）
E1. MoveTo（移动到坐标）

npc:MoveTo(loc) -> string（异步，常见 Success/Fail）
说明：让 NPC 移动到目标位置。
参数：

loc：FVector

示例：

local r = npcA:MoveTo({X=100, Y=0, Z=0})


推荐用法：

npcA:MoveTo(locA)
World.Wait(0.9)


常见错误：

MoveTo 后立即对话，没有 Wait

E2. MoveToActor（移动到目标 Actor）

npc:MoveToActor(target) -> string（异步）
说明：让 NPC 走向目标 Actor。
参数：

target：Actor

示例：

local r = npcA:MoveToActor(player)

E3. Follow（跟随）

npc:Follow(target, dist) -> nil
说明：NPC 跟随目标 Actor。
参数：

target：Actor

dist：number

示例：

npcA:Follow(player, 180)

E4. StopFollow（停止跟随）

npc:StopFollow() -> nil
说明：停止 Follow。
参数：无

示例：

npcA:StopFollow()

E5. LookAt（朝向目标）

npc:LookAt(target) -> nil
说明：NPC 面向目标 Actor。
参数：

target：Actor

示例：

npcA:LookAt(player)


推荐用法：

npcA:MoveTo(locA)
World.Wait(0.8)
npcA:LookAt(player)

E6. PlayAnim（播放动画）

npc:PlayAnim(animName) -> nil（异步）
说明：播放一次动画。**重要：animName必须来自动画素材库，不能随意创建动画名称**。
参数：

animName：string（必须使用动画素材库中的名称，如"Wave"、"Happy"、"Drink"等）

可用动画列表：
- 基础：Idle, Walk, Run
- 跳跃：Jump_01, Jump_02, Jump_03
- 战斗：Melee Attack_01/02/03, Ranged Attack_01/02/03
- 情绪：Happy, Admiring, Shy, Frustrated, Scared
- 交互：Pick Up, Hide, Eat, Drink, Sleep, Sit, Dialogue, Give, Point To, Wave, Sing, Dance

示例：

npcA:PlayAnim("Wave")
npcA:PlayAnim("Happy")
npcA:PlayAnim("Drink")


推荐用法：

npcA:PlayAnim("Wave")
World.Wait(0.6)


常见错误：

使用不存在的动画名称（如"Alice_Wave"、"Angry"等）
动画名称不在素材库中

E7. PlayAnimLoop（循环动画）

npc:PlayAnimLoop(animName, time) -> nil
说明：循环播放动画一段时间。
参数：

animName：string

time：number

示例：

npcA:PlayAnimLoop("IdleTalk", 3.0)

E8. ApproachAndSay（靠近并说话）

npc:ApproachAndSay(target, text) -> nil（异步）
说明：NPC 自动走向目标并说话。
参数：

target：Actor

text：string（对话内容，直接使用引号包裹，不要使用方括号）

示例：

npcA:ApproachAndSay(player, "等等！你能帮我一下吗？")


推荐用法：

npcA:ApproachAndSay(player, "你看起来不像本地人。")
World.Wait(1.0)


常见错误：

对话内容使用了方括号（错误：`"[文本]"`，正确：`"文本"`）

E9. SetAsHostile（敌对化）

npc:SetAsHostile() -> string（异步，缺组件时返回 Victory）
说明：将 NPC 设置为敌对状态。
参数：无

示例：

local r = npcA:SetAsHostile()


推荐用法：

npcA:SetAsHostile()
World.Wait(0.4)
UI.Toast("对方突然翻脸！")

E10. SetAsAlly（盟友化）

npc:SetAsAlly() -> nil
说明：将 NPC 设置为友方。
参数：无

示例：

npcA:SetAsAlly()

E11. GiveItem（给予物品）

npc:GiveItem(id, count) -> nil
说明：给予玩家物品。ID 必须存在于 DT_Items.csv。

gameplay_knowledge_base


参数：

id：string（例如 "Money"）

count：int

示例：

npcA:GiveItem("Money", 10)


推荐用法：

npcA:GiveItem("Money", 10)
UI.Toast("你获得了 Money x10")

E12. GiveEquip（给予装备）

npc:GiveEquip(id, count) -> nil
说明：给予玩家装备。ID 必须存在于 datatable。
参数：

id：string

count：int

示例：

npcA:GiveEquip("Helmet", 1)

E13. GiveWeapon（给予武器）

npc:GiveWeapon(id, count) -> nil
说明：给予玩家武器。ID 必须存在于 datatable。
参数：

id：string

count：int

示例：

npcA:GiveWeapon("TestSword", 1)

F. Time 模块（环境时间控制，可选）
F1. 获取时间信息

Time.GetInfo() -> table
说明：获取时间信息 table。
参数：无

示例：

local t = Time.GetInfo()

F2. 判断夜晚

Time.IsNight() -> bool
说明：判断是否为夜晚。
参数：无

示例：

if Time.IsNight() then
    UI.Toast("夜色更危险。")
end

G. Math 模块（随机性与涌现关键）
G1. 随机整数

Math.RandInt(min, max) -> int
说明：生成随机整数。
参数：

min：int

max：int

示例：

local v = Math.RandInt(1, 10)

G2. 概率触发

Math.Chance(p) -> bool
说明：以概率 p 返回 true。
参数：

p：number（0~1）

示例：

if Math.Chance(0.3) then
    UI.Toast("突然发生意外！")
end

G3. 距离计算

Math.Dist(a, b) -> number
说明：计算两点距离。
参数：

a：FVector

b：FVector

示例：

local d = Math.Dist(ppos, base)

H. Encounter 完整模板（可直接用于生成）
H1. 最小可运行 Encounter 模板（1 NPC + 2 分支）
World.SpawnEncounter(
    {X=0, Y=0, Z=0},
    300,
    {
        ["Tag_A"] = "NPC_Base"
    },
    "EnterVolume",
    [[
local player = World.GetByID("Player")
local npcA = World.GetByID("Tag_A")

if not player or not player:IsValid() then return end
if not npcA or not npcA:IsValid() then return end

local ppos = player:GetPos()
local base = {X=ppos.X + 200, Y=ppos.Y, Z=ppos.Z}

npcA:MoveTo(base)
World.Wait(0.9)

npcA:LookAt(player)
World.Wait(0.4)

UI.ShowDialogue("陌生人", "你能停一下吗？我需要你帮个忙。")
World.Wait(0.6)

local r = UI.AskMany("你要怎么回应？", {"帮忙", "拒绝"})

if r == 1 then
    UI.ShowDialogue("陌生人", "太好了！我就知道你是个可靠的人。")
    World.Wait(0.5)
    npcA:GiveItem("Money", 15)
    UI.Toast("你获得了 Money x15")
else
    UI.ShowDialogue("陌生人", "好吧……我不该期待什么。")
    World.Wait(0.5)
    UI.Toast("对方失望地离开了。")
end

World.Wait(0.8)

System.Exit()
    ]]
)

I. Encounter 常见拼装套路（RAG Pattern Chunk）
I1. "冲突升级"套路（Conflict Escalation）

推荐拼装顺序：

NPC MoveTo 站位

NPC LookAt

NPC PlayAnim("Angry")

UI.ShowDialogue 引发矛盾

UI.AskMany 选择

分支：平息 / 升级战斗

SpawnEnemy 或 GiveItem

System.Exit

I2. "随机意外"套路（Emergent Random Event）

推荐写法：

if Math.Chance(0.4) then
    World.PlaySound("SFX_Hit", base)
    World.PlayFX("FX_Explosion", base)
    UI.Toast("一阵骚动突然爆发！")
end
