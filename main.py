import streamlit as st
import datetime
# 旧（今はエラーになる可能性がある）
from langchain.chat_models import ChatOpenAI
# 新（推奨）
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from langchain.tools import tool

# --- Streamlit UI ---
st.set_page_config(page_title="外出後押しAI", page_icon="🚶")
st.title("🚶 ゆるく外出を後押しするパーソナルエージェントAI")
st.markdown("コロナ後、家にこもりがちになったあなたへ。外出のきっかけを、やさしく提案します。")

api_key = st.text_input("🔑 OpenAI APIキーを入力してください", type="password")

mood = st.selectbox("🧠 今の気分は？", ["疲れてる", "まあまあ", "元気"])
genre = st.multiselect("🎯 興味あるジャンル（複数選択OK）", ["カフェ", "自然", "温泉", "街歩き", "運動", "映画", "美術館"])
time_slot = st.selectbox("🕐 出かけたい時間帯は？", ["午前", "午後", "夕方"])
location = st.text_input("📍 出発地（市区町村や最寄駅）", placeholder="例：新宿区、京都駅など")

submit = st.button("🚀 プランを作成する")

# --- LangChain Tools定義 ---

@tool
def mood_to_level(mood: str) -> str:
    """気分に応じたアクティビティ強度（低・中・高）を返す"""
    if "疲" in mood:
        return "低"
    elif "まあまあ" in mood:
        return "中"
    else:
        return "高"

@tool
def generate_plan(data: str) -> str:
    """ジャンル・出発地・時間帯・強度からお出かけプランを提案する"""
    return f"""
【プラン例】
- 出発地: {data}
- 内容: 近場で静かなカフェに立ち寄り、その後ゆるく散歩。自然が感じられる公園がおすすめです。
- スケジュール: 14:00 出発 → 14:30 カフェ → 16:00 散歩 → 17:30 帰宅
"""

@tool
def encouragement_message(mood: str) -> str:
    """気分に応じたやさしい応援メッセージを返す"""
    if "疲" in mood:
        return "「疲れているときこそ、少しの外出でリセットできます。無理なく、一歩だけ踏み出してみましょう。」"
    elif "まあまあ" in mood:
        return "「ちょっとしたお出かけが、気分の切り替えになります。新しい風を感じてみましょう。」"
    else:
        return "「今の元気を使って、楽しい体験に出かけましょう！」"

# --- エージェント実行 ---
if submit:
    if not api_key:
        st.warning("OpenAI APIキーを入力してください。")
    elif not genre or not location:
        st.warning("ジャンルと出発地は必須です。")
    else:
        with st.spinner("AIが外出プランを考えています..."):

            # LLM初期化
            llm = ChatOpenAI(
                openai_api_key=api_key,
                model="gpt-4o",
                temperature=0.7
            )

            tools = [mood_to_level, generate_plan, encouragement_message]
            agent = initialize_agent(
                tools,
                llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True
            )

            # エージェントへのプロンプト（Run）
            prompt = f"""
あなたは家にこもりがちな人を励まし、外出のきっかけを提案するやさしいエージェントです。

以下の情報を元に：

1. 活動強度（低・中・高）を推定
2. 外出プランを1件作成（{location} 出発、{', '.join(genre)} 目的、{time_slot}に活動）
3. 応援メッセージを添える

最終的に「プランタイトル、スケジュール、おすすめ理由、応援メッセージ」の形式でまとめてください。

気分: {mood}
ジャンル: {', '.join(genre)}
時間帯: {time_slot}
出発地: {location}
"""

            result = agent.run(prompt)

            # 表示とダウンロード
            st.success("✅ プラン完成！")
            st.markdown("### 📝 外出プラン")
            st.markdown(result)

            today = datetime.date.today().isoformat()
            filename = f"outing_plan_{today}.txt"
            st.download_button(
                label="📄 プランをダウンロード",
                data=result,
                file_name=filename,
                mime="text/plain"
            )
