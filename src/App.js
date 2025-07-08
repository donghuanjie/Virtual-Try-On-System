import React, { useState } from 'react';
import './App.css';

// 动态获取API基础URL
const getApiBaseUrl = () => {
  // 如果是开发环境，使用当前窗口的hostname和后端端口
  const hostname = window.location.hostname;
  return `http://${hostname}:8000`;
};

const API_BASE_URL = getApiBaseUrl();

function App() {
  const [formData, setFormData] = useState({
    clothingImage: null,
    // Basic information
    gender: '',
    age: '',
    height: '',
    weight: '',
    nationality: '', // Added nationality field
    // Camera settings
    shotType: 'full_body',  // 新增：拍摄类型
    angle: 'front',         // 新增：拍摄角度
    // Optional descriptions
    actionDescription: '', // Added action description
    sceneDescription: ''   // Added scene description
  });

  const [previewImage, setPreviewImage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [generatedImage, setGeneratedImage] = useState(null);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  
  // 新增状态管理
  const [currentStep, setCurrentStep] = useState(0);
  const [modelImage, setModelImage] = useState(null); // 存储中间生成的模特图片
  const [processSteps, setProcessSteps] = useState([
    { id: 1, name: '📝 ModelDescriptionAgent', description: '智能分析模特参数，生成详细描述', status: 'waiting' },
    { id: 2, name: '🎨 ModelGenerationAgent', description: '基于描述生成专属模特图像', status: 'waiting' },
    { id: 3, name: '👕 ImageMergeAgent', description: '将服装与模特完美融合', status: 'waiting' }
  ]);
  
  // 进度状态管理 - 支持两个生成步骤
  const [modelGenerationProgress, setModelGenerationProgress] = useState(0);
  const [isModelGenerating, setIsModelGenerating] = useState(false);
  const [imageMergeProgress, setImageMergeProgress] = useState(0);
  const [isImageMerging, setIsImageMerging] = useState(false);
  
  // 自定义弹窗状态
  const [showModal, setShowModal] = useState(false);
  const [modalConfig, setModalConfig] = useState({
    title: '',
    message: '',
    icon: '',
    confirmText: '确定',
    onConfirm: () => setShowModal(false)
  });

  // 创建真实的进度模拟函数
  const createProgressSimulation = (setProgress, targetTime = 30000) => {
    const interval = 500; // 每500ms更新一次
    const maxProgress = 90; // 最大进度90%
    const totalSteps = targetTime / interval; // 总步数
    const baseIncrement = maxProgress / totalSteps; // 基础增长量
    
    let currentProgress = 0;
    let step = 0;
    
    const progressInterval = setInterval(() => {
      step++;
      
      // 使用指数衰减公式让进度条开始快，后面慢
      const progressFactor = 1 - Math.exp(-step / (totalSteps * 0.3));
      const targetProgress = maxProgress * progressFactor;
      
      // 添加一些随机波动让进度更自然
      const randomFactor = 0.5 + Math.random() * 0.5; // 0.5-1.0
      const increment = (targetProgress - currentProgress) * 0.1 * randomFactor;
      
      currentProgress = Math.min(currentProgress + increment, maxProgress);
      setProgress(Math.floor(currentProgress));
      
      // 如果达到目标时间，停在90%
      if (step >= totalSteps) {
        setProgress(90);
        clearInterval(progressInterval);
      }
    }, interval);
    
    return progressInterval;
  };

  // 显示错误弹窗的函数
  const showErrorModal = (title, message, icon = '❌') => {
    setModalConfig({
      title,
      message,
      icon,
      confirmText: '我知道了',
      onConfirm: () => setShowModal(false)
    });
    setShowModal(true);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: value
    }));
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFormData(prevData => ({
        ...prevData,
        clothingImage: file
      }));
      
      // 创建预览图片
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreviewImage(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };



  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // 检查必须上传衣服图片
    if (!formData.clothingImage) {
      setError('请先上传上衣图片');
      return;
    }
    
    setIsLoading(true);
    setGeneratedImage(null);
    setModelImage(null);
    setError(null);
    setCurrentStep(0);
    
    // 重置所有步骤状态
    setProcessSteps(prev => prev.map(step => ({ ...step, status: 'waiting' })));

    try {
      // 第一步：验证衣服图片
      console.log('🔍 Validating clothing image...');
      setSuccessMessage('🔍 正在验证上传的衣服图片...');
      
      const clothingCheckResponse = await fetch(`${API_BASE_URL}/api/check-clothing`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          clothingImage: previewImage
        })
      });
      
      if (!clothingCheckResponse.ok) {
        throw new Error(`Clothing validation failed: ${clothingCheckResponse.status}`);
      }
      
      const checkResult = await clothingCheckResponse.json();
      
      if (!checkResult.success || !checkResult.result.valid) {
        // 衣服检测失败，显示弹窗提示
        const errorMsg = checkResult.result.error_message || '图片不符合要求';
        showErrorModal(
          '图片验证失败',
          `${errorMsg}\n\n请上传包含单件上衣的清晰图片（不含模特）。`,
          '📷'
        );
        setSuccessMessage(null); // 清除之前的验证中消息
        setError('图片验证失败，请重新上传符合要求的上衣图片');
        return;
      }
      
      console.log('✅ Clothing validation passed');
      setSuccessMessage('✅ 上衣图片验证通过！');
      
      // 短暂延迟让用户看到验证成功的消息
      await new Promise(resolve => setTimeout(resolve, 1000));

      // 准备模特参数
      const modelParams = {
        gender: formData.gender,
        age: formData.age,
        nationality: formData.nationality,
        height: formData.height,
        weight: formData.weight,
        camera: {
          shot_type: formData.shotType,
          angle: formData.angle
        },
        actionDescription: formData.actionDescription,
        sceneDescription: formData.sceneDescription
      };

      console.log('Starting step-by-step generation with params:', modelParams);

      // 更新步骤状态的函数
      const updateStep = (stepIndex, status) => {
        setCurrentStep(stepIndex);
        setProcessSteps(prev => prev.map((step, index) => ({
          ...step,
          status: index < stepIndex ? 'completed' : index === stepIndex ? status : 'waiting'
        })));
      };

      // 第一步：ModelDescriptionAgent（快速完成）
      updateStep(0, 'processing');
      await new Promise(resolve => setTimeout(resolve, 1000)); // 短暂延迟用于UI显示
      updateStep(0, 'completed');
      
      // 第二步：ModelGenerationAgent - 生成模特图片
      updateStep(1, 'processing');
      setIsModelGenerating(true);
      setModelGenerationProgress(0);
      
      // 启动真实的进度模拟 - 30秒到90%
      const modelProgressInterval = createProgressSimulation(setModelGenerationProgress, 30000);
      
      console.log('🎨 Calling model generation API...');
      const modelResponse = await fetch(`${API_BASE_URL}/api/generate-model-only`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(modelParams)
      });
      
      // 清除进度模拟，完成到100%
      clearInterval(modelProgressInterval);
      setModelGenerationProgress(100);
      setIsModelGenerating(false);

      if (!modelResponse.ok) {
        throw new Error(`Model generation failed: ${modelResponse.status}`);
      }

      const modelResult = await modelResponse.json();

      if (modelResult.success && modelResult.result.model_image.success) {
        // 模特生成成功，立即显示模特图片
        updateStep(1, 'completed');
        const modelImageUrl = `${API_BASE_URL}${modelResult.result.model_image.image_url}`;
        setModelImage(modelImageUrl);
        console.log('✅ Model image generated and displayed:', modelImageUrl);
        
        // 显示中间成功消息
        setSuccessMessage('🎨 专属模特生成完成！正在进行试衣合并...');
        
        // 等待用户查看模特图片
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // 第三步：ImageMergeAgent - 图像合并
        updateStep(2, 'processing');
        setSuccessMessage('👕 正在进行虚拟试衣合并...');
        setIsImageMerging(true);
        setImageMergeProgress(0);
        
        // 启动图像合并进度模拟 - 30秒到90%
        const mergeProgressInterval = createProgressSimulation(setImageMergeProgress, 30000);
        
        console.log('👕 Calling clothing merge API...');
        const mergeResponse = await fetch(`${API_BASE_URL}/api/merge-clothing-only`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            clothingImage: previewImage, // base64图片数据
            modelImagePath: modelResult.result.model_image.image_path,
            shot_type: formData.shotType === 'full_body' ? '全身' : '半身',
            angle: formData.angle === 'front' ? '正面' : '侧面',
            pose_description: formData.actionDescription || '自然站立姿势',
            scene_description: formData.sceneDescription || '简约工作室背景'
          })
        });
        
        // 清除进度模拟，完成到100%
        clearInterval(mergeProgressInterval);
        setImageMergeProgress(100);
        setIsImageMerging(false);

        if (!mergeResponse.ok) {
          throw new Error(`Clothing merge failed: ${mergeResponse.status}`);
        }

        const mergeResult = await mergeResponse.json();

        if (mergeResult.success && mergeResult.result.final_image.success) {
          // 合并成功，显示最终结果
          updateStep(2, 'completed');
          
          // 保存最终结果
          setGeneratedImage({
            result: {
              generated_image: mergeResult.result.final_image
            }
          });
          
          setSuccessMessage('🎉 虚拟试穿完成！所有步骤都已成功完成');
          console.log('✅ Final try-on image generated:', mergeResult.result.final_image.image_url);
        } else {
          // 合并失败，但模特图片成功了
          updateStep(2, 'failed');
          setSuccessMessage('🎨 模特生成成功，但试衣合并失败');
          setError(`图像合并失败: ${mergeResult.error || '未知错误'}`);
        }
      } else {
        // 模特生成失败
        updateStep(1, 'failed');
        throw new Error(modelResult.error || '模特生成失败');
      }

    } catch (error) {
      console.error('Generation error:', error);
      setError(`生成失败: ${error.message}`);
      // 设置当前步骤为失败状态
      setProcessSteps(prev => prev.map((step, index) => 
        index === currentStep ? { ...step, status: 'failed' } : step
      ));
      // 重置所有进度状态
      setIsModelGenerating(false);
      setModelGenerationProgress(0);
      setIsImageMerging(false);
      setImageMergeProgress(0);
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      clothingImage: null,
      gender: '',
      age: '',
      height: '',
      weight: '',
      nationality: '',
      shotType: 'full_body',  // 重置相机参数
      angle: 'front',         // 重置相机参数
      actionDescription: '',
      sceneDescription: ''
    });
    setPreviewImage(null);
    setGeneratedImage(null);
    setModelImage(null);
    setError(null);
    setSuccessMessage(null);
    setCurrentStep(0);
    setProcessSteps([
      { id: 1, name: '📝 ModelDescriptionAgent', description: '智能分析模特参数，生成详细描述', status: 'waiting' },
      { id: 2, name: '🎨 ModelGenerationAgent', description: '基于描述生成专属模特图像', status: 'waiting' },
      { id: 3, name: '👕 ImageMergeAgent', description: '将服装与模特完美融合', status: 'waiting' }
    ]);
    // 重置所有进度状态
    setIsModelGenerating(false);
    setModelGenerationProgress(0);
    setIsImageMerging(false);
    setImageMergeProgress(0);
  };

  return (
    <div className="App">
      <div className="container">
        <header className="header">
          <h1>🎨 虚拟模特试衣系统</h1>
          <p>上传上衣图片，设置模特参数，AI智能生成专属试衣效果</p>
        </header>

        <div className="main-content">
          <form onSubmit={handleSubmit} className="form">
            {/* 衣服图片上传区域 */}
            <div className="form-section">
              <h2>📷 上衣图片</h2>
              <div className="image-upload-area">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageChange}
                  className="file-input"
                  id="clothing-image"
                  required
                />
                <label htmlFor="clothing-image" className="file-label">
                  {previewImage ? (
                    <img src={previewImage} alt="预览" className="preview-image" />
                  ) : (
                    <div className="upload-placeholder">
                      <span className="upload-icon">📁</span>
                      <span>点击上传上衣图片（必需）</span>
                      <span className="upload-hint">支持 JPG, PNG, GIF，系统将自动分析衣服特征</span>
                    </div>
                  )}
                </label>
              </div>
            </div>

            {/* 模特基本信息 */}
            <div className="form-section">
              <h2>👤 模特基本信息</h2>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="gender">性别 *</label>
                  <select
                    id="gender"
                    name="gender"
                    value={formData.gender}
                    onChange={handleInputChange}
                    required
                  >
                    <option value="">请选择性别</option>
                    <option value="male">男性</option>
                    <option value="female">女性</option>
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="age">年龄 *</label>
                  <input
                    type="number"
                    id="age"
                    name="age"
                    value={formData.age}
                    onChange={handleInputChange}
                    placeholder="25"
                    min="16"
                    max="60"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="nationality">国籍</label>
                  <select
                    id="nationality"
                    name="nationality"
                    value={formData.nationality}
                    onChange={handleInputChange}
                  >
                    <option value="">请选择国籍</option>
                    <option value="Chinese">中国</option>
                    <option value="American">美国</option>
                    <option value="European">欧洲</option>
                    <option value="African">非洲</option>
                  </select>
                </div>
              </div>
            </div>

            {/* 体型参数 */}
            <div className="form-section">
              <h2>📏 体型参数</h2>
              <p style={{color: '#666', fontSize: '0.9rem', marginBottom: '15px'}}>
                💡 只需输入身高体重，系统会根据性别和BMI自动推测合适的三围比例和体型
              </p>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="height">身高 (cm) *</label>
                  <input
                    type="number"
                    id="height"
                    name="height"
                    value={formData.height}
                    onChange={handleInputChange}
                    min="150"
                    max="200"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="weight">体重 (kg) *</label>
                  <input
                    type="number"
                    id="weight"
                    name="weight"
                    value={formData.weight}
                    onChange={handleInputChange}
                    min="40"
                    max="150"
                    required
                  />
                </div>
              </div>
            </div>

            {/* 相机参数 */}
            <div className="form-section">
              <h2>📸 相机参数</h2>
              <p style={{color: '#666', fontSize: '0.9rem', marginBottom: '15px'}}>
                💡 选择拍摄类型和角度，模特将自动保持站立姿势
              </p>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="shotType">拍摄类型 *</label>
                  <select
                    id="shotType"
                    name="shotType"
                    value={formData.shotType}
                    onChange={handleInputChange}
                    required
                  >
                    <option value="full_body">🎯 全身拍摄</option>
                    <option value="half_body">👤 半身拍摄</option>
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="angle">拍摄角度 *</label>
                  <select
                    id="angle"
                    name="angle"
                    value={formData.angle}
                    onChange={handleInputChange}
                    required
                  >
                    <option value="front">⬆️ 正面视角</option>
                    <option value="side">↗️ 侧面视角</option>
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="pose">姿势要求</label>
                  <input
                    type="text"
                    id="pose"
                    value="🕴️ 站立姿势"
                    disabled
                    style={{
                      backgroundColor: '#f5f5f5',
                      color: '#666',
                      cursor: 'not-allowed'
                    }}
                  />
                  <small style={{color: '#999', fontSize: '0.8rem'}}>
                    * 模特始终保持站立姿势，无法修改
                  </small>
                </div>
              </div>
            </div>

            {/* 可选描述 */}
            <div className="form-section optional-section">
              <h2>🎭 个性化设置（可选）</h2>
              <div className="form-group">
                <label htmlFor="actionDescription">人物动作描述</label>
                <input
                  type="text"
                  id="actionDescription"
                  name="actionDescription"
                  value={formData.actionDescription}
                  onChange={handleInputChange}
                  placeholder="例如：自信地站立，双手叉腰，微笑看向镜头"
                />
              </div>
              <div className="form-group">
                <label htmlFor="sceneDescription">场景描述</label>
                <input
                  type="text"
                  id="sceneDescription"
                  name="sceneDescription"
                  value={formData.sceneDescription}
                  onChange={handleInputChange}
                  placeholder="例如：淘宝带货海报风格，纯白色背景，专业摄影棚灯光"
                />
              </div>
            </div>

            <div className="button-group">
              <button type="button" onClick={resetForm} className="btn btn-secondary">
                🔄 重置表单
              </button>
              <button type="submit" className="btn btn-primary" disabled={isLoading}>
                {isLoading ? '🎨 AI生成中...' : '✨ 生成试衣效果'}
              </button>
            </div>
          </form>

          <div className="result-section">
            <h2>🖼️ 生成结果</h2>
            
            {isLoading && (
              <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>🤖 Multi-Agent智能系统正在生成...</p>
                <div className="agent-progress">
                  {processSteps.map((step, index) => (
                    <div key={step.id} className={`progress-step ${step.status}`}>
                      <div className="step-header">
                        <div className="step-icon">
                          {step.status === 'completed' && '✅'}
                          {step.status === 'processing' && '🔄'}
                          {step.status === 'waiting' && '⏳'}
                          {step.status === 'failed' && '❌'}
                        </div>
                        <div className="step-info">
                          <h4>{step.name}</h4>
                          <p>{step.description}</p>
                          <div className="step-status">
                            {step.status === 'completed' && '✅ 完成'}
                            {step.status === 'processing' && '🔄 处理中...'}
                            {step.status === 'waiting' && '⏳ 等待中'}
                            {step.status === 'failed' && '❌ 失败'}
                          </div>
                        </div>
                      </div>
                      
                      {/* 显示详细进度信息 */}
                      {step.status === 'processing' && (
                        <div className="step-details">
                          {index === 0 && '正在分析模特参数，生成智能描述...'}
                          {index === 1 && (
                            <div className="model-generation-progress">
                              <p>正在使用AI生成专属模特图像...</p>
                              {isModelGenerating && (
                                <div className="simple-progress">
                                  <div className="simple-progress-bar">
                                    <div 
                                      className="simple-progress-fill" 
                                      style={{ width: `${modelGenerationProgress}%` }}
                                    ></div>
                                  </div>
                                  <p className="simple-progress-text">
                                    {Math.round(modelGenerationProgress)}% - 🎨 AI正在绘制您的专属模特...
                                  </p>
                                </div>
                              )}
                            </div>
                          )}
                          {index === 2 && (
                            <div className="image-merge-progress">
                              <p>正在将模特与服装完美融合...</p>
                              {isImageMerging && (
                                <div className="simple-progress">
                                  <div className="simple-progress-bar">
                                    <div 
                                      className="simple-progress-fill" 
                                      style={{ width: `${imageMergeProgress}%` }}
                                    ></div>
                                  </div>
                                  <p className="simple-progress-text">
                                    {Math.round(imageMergeProgress)}% - 👕 AI正在完美融合模特与服装...
                                  </p>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}

                </div>

                {/* 在加载过程中，如果模特图片已生成，则在这里展示 */}
                {modelImage && (
                  <div className="intermediate-result" style={{ marginTop: '20px', textAlign: 'center' }}>
                    <h5>🎨 专属模特已生成！</h5>
                    <img src={modelImage} alt="生成的模特" className="model-preview" />
                  </div>
                )}
              </div>
            )}

            {error && (
              <div className="error-container">
                <span className="error-icon">❌</span>
                <p>{error}</p>
              </div>
            )}

            {successMessage && (
              <div className="success-container">
                <span className="success-icon">✅</span>
                <p>{successMessage}</p>
              </div>
            )}

            {generatedImage && generatedImage.result && (
              <div className="result-content">
                {generatedImage.result.generated_image && generatedImage.result.generated_image.success ? (
                  // 显示生成的图片
                  <div className="generated-images-section">
                    <h3>🎉 AI生成结果</h3>
                    
                    <div className="images-gallery">
                      {/* 如果有模特图片，先显示 */}
                      {modelImage && (
                        <div className="image-item model-item">
                          <h4>🎨 第一步：生成专属模特</h4>
                          <div className="image-container">
                            <img 
                              src={modelImage} 
                              alt="生成的模特图像" 
                              className="generated-image model-image"
                            />
                          </div>
                          <p className="image-description">基于您的参数生成的专属模特形象</p>
                        </div>
                      )}
                      
                      {/* 最终试穿图片 */}
                      <div className="image-item final-item">
                        <h4>👕 第二步：试穿效果</h4>
                        <div className="image-container">
                          <img 
                            src={`${API_BASE_URL}${generatedImage.result.generated_image.image_url}`} 
                            alt="最终试穿效果图" 
                            className="generated-image final-image"
                            onError={(e) => {
                              console.error('图片加载失败:', e);
                              setError('图片加载失败，请检查服务器状态');
                            }}
                          />
                        </div>
                        <div className="image-info">
                          <p>📁 文件名: {generatedImage.result.generated_image.filename}</p>
                          <p>📊 文件大小: {generatedImage.result.generated_image.file_size_kb} KB</p>
                          <p>🎯 生成状态: 成功</p>
                          <p>⏰ 生成时间: {new Date(generatedImage.result.generated_image.timestamp).toLocaleString()}</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="action-buttons">
                      <button 
                        className="btn btn-primary" 
                        onClick={() => {
                          // 在新窗口打开最终试穿图片
                          window.open(`${API_BASE_URL}${generatedImage.result.generated_image.image_url}`, '_blank');
                        }}
                      >
                        🔍 查看大图
                      </button>
                      {modelImage && (
                        <button 
                          className="btn btn-secondary" 
                          onClick={() => {
                            // 在新窗口打开模特图片
                            window.open(modelImage, '_blank');
                          }}
                        >
                          👤 查看模特图片
                        </button>
                      )}
                    </div>
                  </div>
                ) : (
                  // 显示prompt信息和错误说明
                  <div className="prompt-section">
                    <h3>⚠️ 图片生成失败</h3>
                    <div className="error-explanation">
                      <p>AI Agent系统已成功分析并生成了优化的提示词，但图片生成步骤失败。</p>
                      <p>可能的原因：</p>
                      <ul>
                        <li>OpenAI API配置问题</li>
                        <li>网络连接问题</li>
                        <li>API配额不足</li>
                      </ul>
                    </div>
                    <div className="prompt-text">
                      <h4>生成的优化提示词：</h4>
                      <pre>{generatedImage.result.final_prompt || '暂无prompt信息'}</pre>
                    </div>
                    <button className="btn btn-primary" onClick={() => {
                      navigator.clipboard.writeText(generatedImage.result.final_prompt);
                      alert('提示词已复制到剪贴板！可用于其他AI图片生成工具');
                    }}>
                      📋 复制提示词
                    </button>
                  </div>
                )}

              </div>
            )}

            {!isLoading && !generatedImage && !error && (
              <div className="result-placeholder">
                <div className="placeholder-content">
                  <span className="placeholder-icon">🎭</span>
                  <p>AI生成的虚拟模特图片将在这里显示</p>
                  <p className="placeholder-hint">请先上传上衣图片并填写模特信息</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* 自定义弹窗 */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-icon">{modalConfig.icon}</span>
              <h3 className="modal-title">{modalConfig.title}</h3>
            </div>
            <p className="modal-message">{modalConfig.message}</p>
            <div className="modal-actions">
              <button 
                className="modal-btn modal-btn-primary"
                onClick={modalConfig.onConfirm}
              >
                {modalConfig.confirmText}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App; 