// src/AIcenter.tsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';
import { Layout, Row, Col, Card, Typography, Alert,Avatar, Table, Divider, Select, Spin } from 'antd';
import { EnvironmentOutlined } from '@ant-design/icons';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { GlobeAltIcon,ChartBarIcon } from '@heroicons/react/24/outline';
import { Line } from 'react-chartjs-2';
import {Button, message } from 'antd';

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import './AIcenter.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const { Content } = Layout;
const { Text } = Typography;
const { Option } = Select;

// 站点类型
interface Station {
  name: string;
  lat: number;
  lon: number;
}
// 定义 WaterQuality 类型
interface WaterQuality {
  dissolved_oxygen?: number;
  turbidity?: number;
  pH?: number;
  temperature?: number;
  // 其他水文数据字段
}
// 天气数据类型
interface WeatherData {
  temperature: number;
  windspeed: number;
  winddirection: number;
  time: string;
}
interface WaterData {
  monitor_time: string; // 格式化为 ISO 字符串
  water_quality_level: string;
  temperature: number;
  pH: number;
  dissolved_oxygen: number;
  conductivity: number;
  turbidity: number;
  permanganate_index: number;
  ammonia_nitrogen: number;
  total_phosphorus: number;
  total_nitrogen: number;
  chlorophyll_a: string;
  algae_density: string;
  station_status: string;
}
const stationList: Station[] = [
  { name: '三河镇大桥', lat: 31.6262, lon: 117.2284 },
  { name: '三河镇新大桥', lat: 31.6285, lon: 117.2359 },
  { name: '三胜大队渡口', lat: 31.5824, lon: 117.2596 },
  { name: '兆河入湖区', lat: 31.4948, lon: 117.3007 },
  { name: '入湖口渡口', lat: 31.4889, lon: 117.3064 },
  { name: '双桥河入湖口', lat: 31.4901, lon: 117.3167 },
  { name: '同大排灌站', lat: 31.5847, lon: 117.2583 },
  { name: '希望桥', lat: 31.4926, lon: 117.2621 },
  { name: '庐江缺口', lat: 31.2397, lon: 117.2864 },
  { name: '忠庙', lat: 31.2535, lon: 117.2738 },
  { name: '新河入湖区', lat: 31.3795, lon: 117.3246 },
  { name: '施口', lat: 31.3014, lon: 117.2511 },
  { name: '柘皋大桥', lat: 31.4703, lon: 117.4139 },
  { name: '湖滨(老)', lat: 31.6327, lon: 117.2262 },
  { name: '石堆渡口', lat: 31.4954, lon: 117.2438 },
  { name: '裕溪口', lat: 31.5862, lon: 117.2883 },
  { name: '裕溪口(老)', lat: 31.5865, lon: 117.2904 },
  { name: '西半湖湖心', lat: 31.5837, lon: 117.2329 },
  { name: '通讯塔', lat: 31.5992, lon: 117.2756 },
  { name: '青台山大桥', lat: 31.4422, lon: 117.4568 },
  { name: '黄麓', lat: 31.5617, lon: 117.2830 },
  { name: '殷桥', lat: 31.4720, lon: 117.2338 },
  { name: '新管', lat: 31.4296, lon: 117.3087 },
  { name: '横江大桥', lat: 31.3851, lon: 117.3099 },
  { name: '浦口', lat: 31.5103, lon: 117.2648 },
  { name: '率水大桥', lat: 31.4207, lon: 117.3882 },
  { name: '篁墩', lat: 31.6092, lon: 117.1975 },
  { name: '丁埠大桥', lat: 31.3681, lon: 117.3166 },
  { name: '下楼公路桥', lat: 31.4793, lon: 117.3669 },
  { name: '东坪集', lat: 31.4980, lon: 117.1894 },
  { name: '东湖闸', lat: 31.4661, lon: 117.0320 },
  { name: '五河', lat: 33.1443, lon: 117.8794 },
  { name: '五里闸', lat: 31.5613, lon: 117.2581 },
  { name: '公路桥', lat: 31.4781, lon: 117.2440 },
  { name: '关咀', lat: 31.6225, lon: 117.1809 },
  { name: '刘寨村后', lat: 33.1227, lon: 116.2162 },
  { name: '利辛段', lat: 33.1221, lon: 116.2130 },
  { name: '巢湖西岸', lat: 31.6000, lon: 117.1000 } // 这个是你原示例中额外添加的
];

const data = [
  {
    id: 'fish-9527',
    species: 'moonfish',
    length: '10寸',
    weight: '5kg',
    time: '2024-02-01',
    temp: '0-7℃',
    wind: '东北风 96%',
    humid: '78%',
    level: '5级'
  }
];
// 定义表格数据的类型
interface TableRow {
    species: string;
    description: string,
    juvenile_length_cm: string,
    juvenile_weight_g: string,
    adult_length_cm:string,
    adult_weight_kg:string
}

const AIcenter: React.FC = () => {
  const [selectedStation, setSelectedStation] = useState<Station>(stationList[0]);
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [latestData, setLatestData] = useState<WaterQuality | null>(null); // 最新的水文数据
  const [loading, setLoading] = useState<boolean>(true); // 加载状态
  const [aiSuggestion, setAiSuggestion] = useState<string | null>(null); // 存储 AI 建议
  const [suggestionLoading, setSuggestionLoading] = useState<boolean>(false); // 加载状态
  const [suggestionError, setSuggestionError] = useState<string | null>(null); // 错误信息
  const [waterData, setWaterData] = useState<WaterData | null>(null); // 存储水文数据
  const [waterLoading, setWaterLoading] = useState<boolean>(false); // 加载状态
  const [waterError, setWaterError] = useState<string | null>(null); // 错误信息
  const chartData = {
    labels: ['温度', '光照', '溶氧', '盐度'],
    datasets: [
      {
        label: '当前数值',
        data: [22, 500, 6.5, 32],
        backgroundColor: ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0'],
        borderColor: ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0'],
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { beginAtZero: true },
    },
  };



  
  useEffect(() => {
    const fetchWeather = async () => {
      setLoading(true);
      try {
        const { lat, lon } = selectedStation;
        const res = await axios.get('https://api.open-meteo.com/v1/forecast', {
          params: {
            latitude: lat,
            longitude: lon,
            hourly: 'temperature_2m,relative_humidity_2m,wind_speed_10m',
            current_weather: true,
            timezone: 'auto'
          }
        });
        setWeather(res.data.current_weather);
      } catch (error) {
        console.error('获取天气失败:', error);
        setWeather(null);
      }
      setLoading(false);
    };
    fetchWeather();
  }, [selectedStation]);
  // 获取 AI 建议（调用后端 API）
  const fetchAiSuggestion = async () => {
    if (!weather) {
      setAiSuggestion('暂无气象数据，无法生成建议');
      return;
    }

    setSuggestionLoading(true);
    setSuggestionError(null); // 清除之前的错误
    try {
      // 调用后端 API 获取 AI 建议
      const response = await axios.post('http://localhost:5000/api/get-advice', {
        temperature: weather.temperature,
        windspeed: weather.windspeed,
        winddirection: weather.winddirection,
      });

      if (response.data && response.data.advice) {
        setAiSuggestion(response.data.advice);
      } else {
        setAiSuggestion('大模型未返回有效建议');
      }
    } catch (error) {
      console.error('获取 AI 建议失败:', error);
      setSuggestionError('获取 AI 建议失败，请稍后重试');
    } finally {
      setSuggestionLoading(false);
    }
  };
  const handleExportWeather = () => {
    if (!weather) {
      message.warning('当前无天气数据可导出');
      return;
    }

    const headers = ['时间', '温度(℃)', '风速(m/s)', '风向(°)'];
    const row = [
      new Date(weather.time).toLocaleString(),
      weather.temperature,
      weather.windspeed,
      weather.winddirection,
    ];

    const csvContent = [headers.join(','), row.join(',')].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'weather_data.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };


   // 根据选择的站点获取水文数据

    // 获取水文数据（调用后端 API）
  const fetchWaterData = async () => {
    setWaterLoading(true);
    setWaterError(null); // 清除之前的错误
    try {
      // 调用后端 API 获取水文数据
      const response = await axios.get(`http://localhost:5000/api/water-data?station=${selectedStation.name}`);
      
      if (response.data && response.data.code === 200) {
        setWaterData(response.data.data);
      } else {
        setWaterError(response.data.message || '获取水文数据失败');
      }
    } catch (error) {
      console.error('获取水文数据失败:', error);
      setWaterError('获取水文数据失败，请稍后重试');
    } finally {
      setWaterLoading(false);
    }
  };
  // 当天气数据更新时，自动获取 AI 建议
  useEffect(() => {
    if (weather) {
      fetchAiSuggestion();
    } else {
      setAiSuggestion(null);
    }
  }, [weather]);
  // 当站点选择变化时，重新获取天气和水文数据
  useEffect(() => {
    setLoading(true);
    setWeather(null);
    setAiSuggestion(null);
    setSuggestionLoading(false);
    setSuggestionError(null);
    setWaterData(null);
    setWaterLoading(false);
    setWaterError(null);

    const fetchInitialData = async () => {
      try {
        // 获取天气数据
        const { lat, lon } = selectedStation;
        const res = await axios.get('https://api.open-meteo.com/v1/forecast', {
          params: {
            latitude: lat,
            longitude: lon,
            hourly: 'temperature_2m,relative_humidity_2m,wind_speed_10m',
            current_weather: true,
            timezone: 'auto'
          }
        });
        setWeather(res.data.current_weather);
      } catch (error) {
        console.error('获取天气失败:', error);
        setWeather(null);
      } finally {
        setLoading(false);
      }

      // 获取 AI 建议
      if (weather) {
        fetchAiSuggestion();
      }

      // 获取水文数据
      fetchWaterData();
    };

    fetchInitialData();
  }, [selectedStation]);

  const { Option } = Select;
const { Text } = Typography;

   const videoSources: string[] = ["/recognition/v1.mp4", "/recognition/v2.mp4", "/recognition/v3.mp4","/recognition/v4.mp4","/recognition/v5.mp4","/recognition/v6.mp4","/recognition/v7.mp4","/recognition/v8.mp4","/recognition/v9.mp4"];
   const imageSources = ['/recognition/img1.jpg', '/recognition/img2.jpg', '/recognition/img3.jpg','/recognition/img4.jpg'];
   const [mode, setMode] = useState<'video' | 'image'>('video');
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [recognitionResult, setRecognitionResult] = useState<{ label: string; confidence: number } | null>(null);
  const [data, setData] = useState<TableRow[]>([]); // 如果叫 data

  const handleUploadAndRecognize = async () => {
    setLoading(true);
    try {
      // 这里模拟上传对应的视频文件给后端。假设你的视频放在public目录，可以直接fetch视频文件转blob
     const url = mode === 'video' ? videoSources[currentVideoIndex] : imageSources[currentImageIndex];
      const response = await fetch(url);
      const blob = await response.blob();
      const fileType = mode === 'video' ? 'video/mp4' : 'image/jpeg';
      const fileName = mode === 'video' ? `video${currentVideoIndex + 1}.mp4` : `image${currentImageIndex + 1}.jpg`;

      const formData = new FormData();
      formData.append('media', new File([blob], fileName, { type: fileType }));
      const res = await fetch('http://localhost:5000/api/upload-media', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (res.ok) {
        setRecognitionResult(data);
          // 将识别结果添加到表格数据中，体长和体重先设为 null
        const newRow = {
            species: data.label,
            description: data.description,
            juvenile_length_cm: data.juvenile_length_cm,
            juvenile_weight_g: data.juvenile_weight_g,
            adult_length_cm:data.adult_length_cm,
            adult_weight_kg: data.adult_weight_kg
        };

       setData([newRow]);
        message.success('识别成功！');
      } else {
        message.error(data.error || '识别失败');
      }
    } catch (error) {
      console.error(error);
      message.error('上传或识别出错');
    }
    setLoading(false);
};
   
  return (
    <Layout className="dashboard-container">
      <Content className="main-content">
        <Row gutter={[16, 16]}>
        


<Col span={16}>
  <Card title="识别结果" bordered={false} className="result-card">
  <div style={{ padding: 20 }}>
      <Text strong>选择识别类型：</Text><br />
      <Select value={mode} onChange={(val) => setMode(val)} style={{ width: 200, margin: '12px 0' }}>
        <Option value="video">识别视频</Option>
        <Option value="image">识别图片</Option>
      </Select>

      {mode === 'video' ? (
        <>
          <Select
            value={currentVideoIndex}
            onChange={(val) => setCurrentVideoIndex(val)}
            style={{ width: 200, marginBottom: 12 }}
          >
            {videoSources.map((_, i) => (
              <Option key={i} value={i}>
                监控视频 {i + 1}
              </Option>
            ))}
          </Select>
          <video
              src={videoSources[currentVideoIndex]}
              controls
              width="100%"
              height="300%"
              style={{ backgroundColor: '#000' }}
          />
        </>
      ) : (
        <>
          <Select
            value={currentImageIndex}
            onChange={(val) => setCurrentImageIndex(val)}
            style={{ width: 200, marginBottom: 12 }}
          >
            {imageSources.map((_, i) => (
              <Option key={i} value={i}>
                监控图片 {i + 1}
              </Option>
            ))}
          </Select>
          <img
            src={imageSources[currentImageIndex]}
            width="100%"
            height="300%"
            style={{ backgroundColor: '#000' }}
          />
        </>
      )}

      <Button type="primary" onClick={handleUploadAndRecognize} loading={loading}>
        上传并识别
      </Button>

      {/* {recognitionResult && (
        <div style={{ marginTop: 20 }}>
          <Text>识别结果：{recognitionResult.label}</Text><br />
          <Text>置信度：{(recognitionResult.confidence * 100).toFixed(2)}%</Text>
        </div>
      )} */}
    </div>


    <Divider />

    <Table
      dataSource={data}
      columns={[
        { title: '鱼种', dataIndex: 'species', key: 'species' },
        { title: '外形特征', dataIndex: 'description', key: 'description' },
        { title: '幼鱼平均体长(cm)', dataIndex: 'juvenile_length_cm', key: 'juvenile_length_cm' },
        { title: '幼鱼平均重量(g)', dataIndex: 'juvenile_weight_g', key: 'juvenile_weight_g' },
        { title: '成年鱼平均体长(cm)', dataIndex: 'adult_length_cm', key: 'adult_length_cm' },
        { title: '成年鱼平均重量(kg)', dataIndex: 'adult_weight_kg', key: 'adult_weight_kg' }

      ]}
      pagination={false}
      rowKey="id"
    />
  </Card>
</Col>


          <Col span={8}>
  <Card title="AI决策" className="status-card">

    {/* 选择站点 */}
    <div style={{ marginBottom: '8px' }}>
      <Text strong>选择站点：</Text>
      <Select
        style={{ width: '100%' }}
        value={selectedStation.name}
        onChange={(value) => {
          const station = stationList.find(s => s.name === value);
          if (station) {
            setSelectedStation(station);
          }
        }}
      >
        {stationList.map((s) => (
          <Option key={s.name} value={s.name}>{s.name}</Option>
        ))}
      </Select>
    </div>

    <Divider />

    {/* 气象数据 */}
    <Text strong>气象数据：</Text>
    {loading ? <Spin /> : (
      weather ? (
        <div style={{ marginTop: '8px' }}>
          <Text>温度：{weather.temperature} ℃</Text><br />
          <Text>风速：{weather.windspeed} km/h</Text><br />
          <Text>风向：{weather.winddirection}°</Text><br />
          <Button type="primary" onClick={handleExportWeather}>
              导出天气数据
          </Button>
        </div>
      ) : <Text>暂无数据</Text>
    )}

     {/* 水文数据 */}
              <Divider />
              <Text strong>水文数据：</Text>
              {waterLoading ? (
                <Spin style={{ marginLeft: '8px' }} />
              ) : waterError ? (
                <Alert message={waterError} type="error" style={{ marginTop: '8px' }} />
              ) : waterData ? (
                <div style={{ marginTop: '8px' }}>
                  <Text>溶解氧：{waterData.dissolved_oxygen} mg/L</Text><br />
                  <Text>浊度：{waterData.turbidity} NTU</Text><br />
                  <Text>pH:{waterData.pH}</Text><br />
                  <Text>温度：{waterData.temperature} ℃</Text><br />
                </div>
              ) : (
                <Text style={{ marginTop: '8px', color: 'gray' }}>暂无水文数据</Text>
              )}
     {/* AI 建议 */}
              <Divider />
              <Text strong>养殖建议：</Text>
              {suggestionLoading ? (
                <Spin style={{ marginLeft: '8px' }} />
              ) : suggestionError ? (
                <Alert message={suggestionError} type="error" style={{ marginTop: '8px' }} />
              ) : aiSuggestion ? (
                <Text style={{ marginTop: '8px', color: 'blue' }}>
                  {aiSuggestion}
                </Text>
              ) : (
                <Text style={{ marginTop: '8px', color: 'gray' }}>暂无建议</Text>
              )}
 
  </Card>
</Col>
</Row>
       
        <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
          <Col span={24}>
            <Card title="监控地图" bordered={false} className="map-card">
              <MapContainer center={[selectedStation.lat, selectedStation.lon]} zoom={8} style={{ height: '400px', width: '100%' }}>
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
                />
                <Marker position={[selectedStation.lat, selectedStation.lon]}>
                  <Popup>{selectedStation.name}</Popup>
                </Marker>
              </MapContainer>
            </Card>
          </Col>
        </Row>
      </Content>
    </Layout>
  );
};

export default AIcenter;