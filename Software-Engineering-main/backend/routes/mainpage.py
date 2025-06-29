from flask import Blueprint, request, jsonify
from models.models import WaterQuality,Farmer,MarineFarmDevice
from extensions import db
from flask import Response
import json
from datetime import datetime

mainpage = Blueprint('mainpage', __name__)
# 获取所有监测点位置信息，去重
@mainpage.route('/api/locations', methods=['GET'])
def get_locations():
    try:
        locations = db.session.query(
            WaterQuality.section_name,
            WaterQuality.province,
            WaterQuality.basin
        ).all()

        seen = set()
        locations_list = []

        for loc in locations:
            # 先清洗字段内容（去掉空格和可能的大小写差异）
            section = loc.section_name.strip()
            province = loc.province.strip()
            basin = loc.basin.strip()

            # 用标准化后的内容去重
            key = (section, province, basin)
            if key not in seen:
                seen.add(key)
                locations_list.append({
                    "section_name": section,
                    "province": province,
                    "basin": basin
                })

        # 返回中文正常显示
        return Response(
            json.dumps({"code": 200, "data": locations_list}, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)})

    
@mainpage.route('/api/farmer_locations', methods=['GET'])
def get_farmer_locations():
    try:
        farmer_name = request.args.get('farmer_name', '').strip()
        if not farmer_name:
            return jsonify({"code": 400, "message": "缺少 farmer_name 参数"})

        # 查询该养殖户负责的所有 section_name
        section_names = db.session.query(Farmer.section_name).filter_by(farmer_name=farmer_name).distinct().all()
        section_names = [s.section_name.strip() for s in section_names]

        if not section_names:
            return jsonify({"code": 200, "data": []})

        # 查询唯一的 section_name, province, basin 组合
        locations = db.session.query(
            WaterQuality.section_name,
            WaterQuality.province,
            WaterQuality.basin
        ).filter(WaterQuality.section_name.in_(section_names)).distinct().all()

        # 构建返回列表
        locations_list = [
            {
                "section_name": loc.section_name.strip(),
                "province": loc.province.strip(),
                "basin": loc.basin.strip()
            }
            for loc in locations
        ]

        return Response(
            json.dumps({"code": 200, "data": locations_list}, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)})


# 获取指
@mainpage.route('/api/latest-data', methods=['GET'])
def get_latest_data():
    try:
        section_name = request.args.get('section_name')
        if not section_name:
            return jsonify({"code": 400, "message": "需要提供section_name参数"})

        section_name = section_name.strip()
        print(f"Debug - 正在查询: '{section_name}'")

        latest_data = WaterQuality.query.filter(
            WaterQuality.section_name.ilike(f"%{section_name}%")
        ).order_by(
            WaterQuality.monitor_time.desc()
        ).first()

        if not latest_data:
            print(f"Debug - 未找到数据: '{section_name}'")
            return jsonify({"code": 404, "message": "未找到相关数据"})

        print(f"Debug - 最新数据: {latest_data.to_dict()}")
        return Response(
            json.dumps({"code": 200, "data": latest_data.to_dict()}, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"code": 500, "message": "服务器内部错误"})




@mainpage.route('/api/range-data', methods=['GET'])
def get_range_data():
    try:
        section_name = request.args.get('section_name')
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')

        if not section_name or not start_time_str or not end_time_str:
            return jsonify({"code": 400, "message": "需要提供 section_name、start_time 和 end_time 参数"})

        section_name = section_name.strip()

        # 解析时间字符串
        try:
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)
        except ValueError:
            return jsonify({"code": 400, "message": "时间格式错误，需为 YYYY-MM-DDTHH:MM:SS"})

        # 查询符合条件的数据（模糊匹配 + 时间范围）
        records = WaterQuality.query.filter(
            WaterQuality.section_name.ilike(f"%{section_name}%"),
            WaterQuality.monitor_time >= start_time,
            WaterQuality.monitor_time <= end_time
        ).order_by(WaterQuality.monitor_time.asc()).all()

        if not records:
            return jsonify({"code": 404, "message": "未找到该时间段内的数据"})

        result = [record.to_dict() for record in records]

        return Response(
            json.dumps({"code": 200, "data": result}, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"code": 500, "message": "服务器内部错误"})


@mainpage.route('/api/device-info', methods=['GET'])
def get_device_info():
    install_location = request.args.get('install_location')

    if not install_location:
        return jsonify({"code": 400, "message": "需要提供 install_location 参数"})

    install_location = install_location.strip()
    print(f"Debug - 正在查询安装位置: '{install_location}'")

    try:
        # 使用 filter() 而不是 filter_by()，这样可以进一步处理复杂的查询逻辑
        devices = MarineFarmDevice.query.filter(MarineFarmDevice.install_location == install_location).all()

        if not devices:
            return jsonify({"code": 404, "message": "未找到相关设备"})

        devices_list = [device.to_dict() for device in devices]

        return Response(
            json.dumps({"code": 200, "data": devices_list}, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )
    except Exception as e:
        print(e)  # 输出异常信息
        return jsonify({"code": 500, "message": "服务器内部错误"})
