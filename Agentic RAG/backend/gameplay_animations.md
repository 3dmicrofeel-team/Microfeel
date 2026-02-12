# 动画素材库（Animation Library）

## 说明

所有NPC的PlayAnim调用必须使用本素材库中的动画名称。禁止使用素材库之外的动画名称。

## 动画列表

### 基础动作
- **Idle** - 待机
- **Walk** - 行走
- **Run** - 奔跑

### 跳跃动作
- **Jump_01** - 起跳_01
- **Jump_02** - 凌空_02
- **Jump_03** - 落地_03

### 战斗动作
- **Melee Attack_01** - 近战普攻_01
- **Melee Attack_02** - 近战普攻_02
- **Melee Attack_03** - 近战普攻_03
- **Ranged Attack_01** - 远程普攻_01
- **Ranged Attack_02** - 远程普攻_02
- **Ranged Attack_03** - 远程普攻_03

### 情绪动作
- **Happy** - 开心
- **Admiring** - 崇拜
- **Shy** - 害羞
- **Frustrated** - 沮丧
- **Scared** - 恐惧

### 交互动作
- **Pick Up** - 拾取
- **Hide** - 躲藏
- **Eat** - 吃
- **Drink** - 喝
- **Sleep** - 睡
- **Sit** - 坐在椅子上
- **Dialogue** - 说话
- **Give** - 给予
- **Point To** - 指向目标
- **Wave** - 挥手打招呼
- **Sing** - 唱歌
- **Dance** - 跳舞

## 使用规范

### 正确示例
```lua
npcA:PlayAnim("Happy")
npcA:PlayAnim("Wave")
npcA:PlayAnim("Drink")
```

### 错误示例
```lua
npcA:PlayAnim("Alice_Wave")  -- 错误：不能添加角色名前缀
npcA:PlayAnim("Happy_01")     -- 错误：不能添加数字后缀
npcA:PlayAnim("Angry")        -- 错误：不在素材库中
```

## 注意事项

1. **严格使用素材库名称**：只能使用上述列表中的动画名称
2. **大小写敏感**：动画名称区分大小写，必须完全匹配
3. **不要添加前缀后缀**：不要添加角色名、数字等前缀后缀
4. **常用动画推荐**：
   - 打招呼：Wave
   - 开心：Happy
   - 害羞：Shy
   - 恐惧：Scared
   - 沮丧：Frustrated
   - 说话：Dialogue
   - 喝酒：Drink
   - 睡觉：Sleep
