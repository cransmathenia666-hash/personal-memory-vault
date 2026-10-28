# 设计依据与边界

资料核对日期：2026-10-26。以下是方法来源，执行本技能不依赖这些产品，也不要求把用户资料上传给它们。产品实现会变化，实际接入前重新核对官方文档。

- [Karpathy：LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)，2026-04-04。借鉴原始来源、派生主题页、规则文件，以及导入／查询／整理的分工；这是一份实践方法，不能当成自动用户理解的效果证明。
- [Letta：MemFS](https://docs.letta.com/concepts/memfs)。借鉴少量核心记忆、按需读取正文、来源历史和版本记录。其默认文件搜索说明向量库不是建库前提；不据此保证普通搜索永远足够。
- [OpenClaw：User model](https://docs.openclaw.ai/concepts/user-model)。借鉴会改变帮助方式的用户模型、带观察日期的偏好，以及明确的有效／被替代状态。此技能不依赖它的文件容量或注入配置。
- [Graphiti：Overview](https://help.getzep.com/graphiti/getting-started/overview)。借鉴事实时间、记录时间、关系变化与来源追溯；个人文件库可先实现相应语义，不必部署图数据库。
- [Filesystem-Based Memory for LLM Agents](https://arxiv.org/abs/2607.26637)，2026-07-29 预印本。在其测试范围内，组织文件降低检索成本，但组织本身未带来更好答案；本技能因此把实际个人化表现与结构检查分开。
- [Useful Memories Become Faulty When Continuously Updated by LLMs](https://arxiv.org/abs/2605.12978)，2026-08-29 修订预印本。其特定任务实验提示反复归纳可能侵蚀有用记忆；借鉴保留原始证据、谨慎合并的原则，不外推为所有记忆更新都有害。

这个技能是一套可验证的工作流程。它不会训练模型参数，不保证记忆永久准确，也不会仅凭文件存在就自动接通不同 Agent 的运行环境。
