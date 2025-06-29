# 从OpenAI库导入OpenAI类，用于与AI模型交互
from openai import OpenAI
# 从Flask库导入Blueprint用于创建蓝图，request用于处理请求，jsonify用于返回JSON响应
from flask import Blueprint, request, jsonify
# 从models.models模块导入WaterQuality模型，用于数据库操作
from models.models import WaterQuality
# 从transformers库导入pipeline，用于加载预训练的AI模型
from transformers import pipeline
# 从PIL库导入Image，用于图像处理
from PIL import Image
# 导入os模块，用于操作系统相关功能
import os
# 导入cv2模块，即OpenCV库，用于计算机视觉任务
import cv2
# 导入random模块，用于生成随机数
import random
# 导入tempfile模块，用于创建临时文件
import tempfile

# 创建一个名为'aicenter'的Flask蓝图，用于组织AI中心的路由
aicenter = Blueprint('aicenter', __name__)

# 初始化OpenAI客户端
# 注意：这里使用的是阿里云百炼平台的兼容模式API
client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key="sk-b6bb661e82b94e96ba90d7c5bb09ca44",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# 定义获取养殖建议的API路由
@aicenter.route('/api/get-advice', methods=['POST'])
def get_advice():
    # 获取请求中的JSON数据
    data = request.get_json()
    
    # 检查必要的气象数据是否存在
    temperature = data.get('temperature')
    windspeed = data.get('windspeed')
    winddirection = data.get('winddirection')

    # 如果缺少任何必要的气象数据，返回错误响应
    if not temperature or not windspeed or not winddirection:
        return jsonify({'error': '缺少必要的气象数据'}), 400

    try:
        # 调用AI模型API获取养殖建议
        completion = client.chat.completions.create(
            # 指定使用的模型
            model="qwen-plus",
            # 设置对话消息
            messages = [
                # 系统消息，设置AI的行为和回答限制
                {"role": "system", "content": "回答不超过50个字！！你是一个养殖渔场的专家，你会通过天气信息和渔场的水文信息给养鱼养殖户智能建议。回答少于50个字！！。"},
                # 用户消息，包含具体的天气信息
                {"role": "user", "content": f"当前温度是 {temperature}℃，风速是 {windspeed} km/h，风向是 {winddirection}°"},  # 示例问题
            ],
        )
        
        # 检查响应中是否包含有效的建议
        if completion.choices and len(completion.choices) > 0:
            # 获取AI生成的建议
            advice = completion.choices[0].message.content
            # 返回建议作为JSON响应
            return jsonify({'advice': advice})
        else:
            # 如果AI模型未返回有效建议，返回错误响应
            return jsonify({'error': 'AI 模型未返回有效建议'}), 500

    except Exception as e:
        # 处理调用OpenAI API时可能出现的异常
        print(f'Error calling OpenAI API: {e}')
        # 返回API调用失败的错误响应
        return jsonify({'error': '获取建议失败，请稍后重试'}), 500

# 定义获取水文数据的API路由
@aicenter.route('/api/water-data', methods=['GET'])
def get_water_data():
    try:
        # 获取前端传递的站点名称参数
        section_name = request.args.get('station')
        # 如果没有提供站点参数，返回错误响应
        if not section_name:
            return jsonify({"code": 400, "message": "需要提供 station 参数"}), 400

        # 查询指定站点的最新水文数据
        # 注意：这里有一个潜在的问题，查询条件应该是section_name，但WaterQuality模型中可能没有这个字段
        # 应该是station_name或其他对应字段
        latest_water_data = WaterQuality.query.filter_by(section_name=section_name).order_by(WaterQuality.monitor_time.desc()).first()

        # 如果没有找到该站点的水文数据，返回错误响应
        if not latest_water_data:
            return jsonify({"code": 404, "message": f"站点 '{section_name}' 暂无数据"}), 404

        # 构造返回的水文数据
        water_data = {
            "dissolved_oxygen": latest_water_data.dissolved_oxygen,
            "turbidity": latest_water_data.turbidity,
            "pH": latest_water_data.pH,
            "temperature": latest_water_data.temperature
        }

        # 返回成功响应和水文数据
        return jsonify({
            "code": 200,
            "data": water_data
        })

    except Exception as e:
        # 处理可能出现的异常
        return jsonify({"code": 500, "message": f"服务器错误: {str(e)}"}), 500
    
# 初始化图像分类器，使用Hugging Face的transformers库中的pipeline
# 使用CLIP模型进行零样本图像分类
classifier = pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")

# 定义鱼类信息字典，包含各种鱼类的描述和生长阶段尺寸信息
fish_info = {
    "Australian tusk": {
        "description": "体型粗壮，嘴部有显著的犬齿状牙齿，身体呈粉红至红褐色，鳞片较大。",
        "juvenile_length_cm": "10-15",
        "juvenile_weight_g": "50-100",
        "adult_length_cm": "40-60",
        "adult_weight_kg": "2-4"
    },
    "Eightbar grouper": {
        "description": "体型厚实，灰褐色体表有8条深色横带，躯干较深，典型石斑鱼体型。",
        "juvenile_length_cm": "10-20",
        "juvenile_weight_g": "100-200",
        "adult_length_cm": "50-80",
        "adult_weight_kg": "3-7"
    },
    "Gemfish": {
        "description": "细长体形，银灰色体表，有锋利的牙齿和大眼睛，典型的深海鱼。",
        "juvenile_length_cm": "15-25",
        "juvenile_weight_g": "200-300",
        "adult_length_cm": "60-100",
        "adult_weight_kg": "3-6"
    },
    "Pink snapper": {
        "description": "体型宽厚，背鳍尖长，体表粉红带银色，眼大，常见于澳大利亚与新西兰沿海。",
        "juvenile_length_cm": "10-20",
        "juvenile_weight_g": "80-150",
        "adult长度_cm": "50-80",
        "adult_weight_kg": "2-6"
    },
    "Smooth stingray": {
        "description": "圆盘状身体，背部灰黑色，无明显棘刺，尾长如鞭。",
        "juvenile_length_cm": "20-30 (盘宽)",
        "juvenile_weight_kg": "1-2",
        "adult_length_cm": "100-200 (盘宽)",
        "adult_weight_kg": "80-200"
    },
    "carp": {
    "description": "体型粗壮，背部隆起，体色呈青灰或黄褐，鳞片较大，口唇肥厚并具触须。",
    "juvenile_length_cm": "5-10",
    "juvenile_weight_g": "20-80",
    "adult_length_cm": "40-70",
    "adult_weight_kg": "2-5"
    },
    "bass": {
    "description": "体形长而略扁，体色呈灰绿色或暗褐色，背鳍明显分裂，口大、下颌突出。",
    "juvenile_length_cm": "6-12",
    "juvenile_weight_g": "30-100",
    "adult_length_cm": "30-50",
    "adult_weight_kg": "1-3"
    },
    "salmon": {
    "description": "体形流线型，体色银白带蓝灰背部，迁徙性强，繁殖期体色变深，雄性有钩状下颌。",
    "juvenile_length_cm": "7-15",
    "juvenile_weight_g": "50-200",
    "adult_length_cm": "60-90",
    "adult_weight_kg": "3-7"
    },
    "catfish": {
    "description": "无鳞鱼类，体表光滑，头宽扁，有胡须状触须，常栖息于底层水域。",
    "juvenile_length_cm": "8-15",
    "juvenile_weight_g": "80-200",
    "adult_length_cm": "50-100",
    "adult_weight_kg": "3-10"
    }
}

# 定义上传媒体文件(图片或视频)进行识别的API路由
@aicenter.route('/api/upload-media', methods=['POST'])
def upload_media():
    # 检查请求中是否包含'media'文件
    if 'media' not in request.files:
        return jsonify({'error': 'No media uploaded'}), 400

    # 获取上传的媒体文件
    media_file = request.files['media']
    # 获取文件名
    filename = media_file.filename

    # 如果上传的是视频文件(.mp4)
    if filename.endswith('.mp4'):
        # 设置标志表示处理的是图片
        is_image = False
        # 创建临时文件保存视频
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp:
            video_path = temp.name
            # 保存上传的视频到临时文件
            media_file.save(video_path)

        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        # 获取视频总帧数
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # 随机选择一帧(确保帧号在有效范围内)
        frame_num = random.randint(0, max(0, frame_count - 1))
        # 设置视频捕获位置到随机选择的帧
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        # 读取选定的帧
        success, frame = cap.read()
        # 释放视频捕获对象
        cap.release()
        # 删除临时视频文件
        os.remove(video_path)

        # 如果无法成功提取视频帧，返回错误响应
        if not success:
            return jsonify({'error': '无法提取视频帧'}), 500

        # 创建临时文件保存提取的视频帧(转换为图片)
        image_path = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg').name
        # 将提取的帧保存为JPG图片
        cv2.imwrite(image_path, frame)
        # 设置标志表示处理的是图片
        is_image = True
        # 定义视频识别任务的候选标签(只识别特定几种鱼类)
        candidate_labels = [
            "Australian tusk", "Eightbar grouper", "Gemfish", "Pink snapper","Smooth stingray"]
        # 定义标签到中文名称的映射
        label_to_chinese = {
            "Australian tusk": "澳洲牙鱼", "Eightbar grouper": "八带石斑鱼", "Gemfish": "宝鱼", "Pink snapper": "粉红鲷",
            "Smooth stingray": "光滑魟"}
    # 如果上传的是图片文件(.jpg, .jpeg, .png)
    elif filename.endswith(('.jpg', '.jpeg', '.png')):
        # 设置标志表示处理的是图片
        is_image=True
        # 创建临时文件保存上传的图片
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp:
            image_path = temp.name
            # 保存上传的图片到临时文件
            media_file.save(image_path)
            # 定义图片识别任务的候选标签(识别更多种类的鱼类)
        candidate_labels = [
                "carp",  "bass", "salmon","catfish"
            ]

        # 定义标签到中文名称的映射
        label_to_chinese = {
            "carp": "鲤鱼", "bass": "鲈鱼", "salmon": "三文鱼", "catfish": "鲶鱼"
        }
    else:
        # 如果上传的文件类型不支持，返回错误响应
        return jsonify({'error': '不支持的文件类型'}), 400

    # 执行通用的图像识别逻辑
    # 使用预训练的分类器对图片进行分类，限制结果为候选标签中的类别
    result = classifier(image_path, candidate_labels=candidate_labels)
    # 从结果中找出得分最高的分类
    best = max(result, key=lambda x: x['score'])
    # 获取最高分分类的中文名称
    label = label_to_chinese.get(best['label'], best['label'])
    # 获取该分类的详细信息(如果有)
    info = fish_info.get(best['label'], {})

    # 返回识别结果，包括标签、置信度、描述和生长阶段尺寸信息
    return jsonify({
        'label': label,
        'confidence': round(best['score'], 4),
        'description': info.get('description', ''),
        'juvenile_length_cm': info.get('juvenile_length_cm', ''),
        'juvenile_weight_g': info.get('juvenile_weight_g', ''),
        'adult_length_cm': info.get('adult_length_cm', ''),
        'adult_weight_kg': info.get('adult_weight_kg', '')
    })