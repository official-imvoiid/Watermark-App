import { useState, useCallback, useRef } from 'react';
import { ImageCanvas, ImageCanvasRef } from './ImageCanvas';
import { ControlPanel } from './ControlPanel';
import { ImageNavigation } from './ImageNavigation';
import { ImageFile, WatermarkSettings, DEFAULT_WATERMARK } from '@/types/watermark';
import { useDynamicFonts } from '@/hooks/useDynamicFonts';
import { toast } from 'sonner';
import { Droplet } from 'lucide-react';
import JSZip from 'jszip';
import { saveAs } from 'file-saver';

export const WatermarkEditor = () => {
  const [images, setImages] = useState<ImageFile[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [imageWatermarks, setImageWatermarks] = useState<Map<string, WatermarkSettings[]>>(new Map());
  const [selectedWatermarkIndex, setSelectedWatermarkIndex] = useState<number | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  
  const folderInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const watermarkImageInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<ImageCanvasRef>(null);

  // Dynamic font loading
  const { fonts: customFonts, loading: fontsLoading } = useDynamicFonts();

  const currentImage = images[currentIndex] || null;
  const currentWatermarks = currentImage 
    ? imageWatermarks.get(currentImage.id) || []
    : [];

  const handleLoadFolder = useCallback(() => {
    folderInputRef.current?.click();
  }, []);

  const handleLoadImage = useCallback(() => {
    imageInputRef.current?.click();
  }, []);

  const handleFolderChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []).filter(file => 
      file.type.startsWith('image/')
    );
    
    if (files.length === 0) {
      toast.error('No images found in folder');
      return;
    }

    const newImages: ImageFile[] = files.map(file => ({
      id: crypto.randomUUID(),
      file,
      url: URL.createObjectURL(file),
      name: file.name,
    }));

    setImages(newImages);
    setCurrentIndex(0);
    setImageWatermarks(new Map());
    setSelectedWatermarkIndex(null);
    toast.success(`Loaded ${files.length} images`);
    
    e.target.value = '';
  }, []);

  const handleImageChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []).filter(file => 
      file.type.startsWith('image/')
    );
    
    if (files.length === 0) return;

    const newImages: ImageFile[] = files.map(file => ({
      id: crypto.randomUUID(),
      file,
      url: URL.createObjectURL(file),
      name: file.name,
    }));

    setImages(prev => [...prev, ...newImages]);
    if (images.length === 0) {
      setCurrentIndex(0);
    }
    toast.success(`Added ${files.length} image(s)`);
    
    e.target.value = '';
  }, [images.length]);

  const handleNavigate = useCallback((index: number) => {
    setCurrentIndex(index);
    setSelectedWatermarkIndex(null);
  }, []);

  const handleAddWatermark = useCallback((type: 'text' | 'image') => {
    if (!currentImage) {
      toast.error('Load an image first');
      return;
    }

    const newWatermark: WatermarkSettings = {
      ...DEFAULT_WATERMARK,
      type,
      text: type === 'text' ? 'Watermark' : '',
    };

    setImageWatermarks(prev => {
      const updated = new Map(prev);
      const existing = updated.get(currentImage.id) || [];
      updated.set(currentImage.id, [...existing, newWatermark]);
      return updated;
    });

    setSelectedWatermarkIndex(currentWatermarks.length);
    
    if (type === 'image') {
      setTimeout(() => watermarkImageInputRef.current?.click(), 100);
    }
  }, [currentImage, currentWatermarks.length]);

  const handleUpdateWatermark = useCallback((index: number, settings: Partial<WatermarkSettings>) => {
    if (!currentImage) return;

    setImageWatermarks(prev => {
      const updated = new Map(prev);
      const existing = updated.get(currentImage.id) || [];
      const newWatermarks = [...existing];
      newWatermarks[index] = { ...newWatermarks[index], ...settings };
      updated.set(currentImage.id, newWatermarks);
      return updated;
    });
  }, [currentImage]);

  const handleDeleteWatermark = useCallback((index: number) => {
    if (!currentImage) return;

    setImageWatermarks(prev => {
      const updated = new Map(prev);
      const existing = updated.get(currentImage.id) || [];
      const newWatermarks = existing.filter((_, i) => i !== index);
      updated.set(currentImage.id, newWatermarks);
      return updated;
    });

    setSelectedWatermarkIndex(null);
  }, [currentImage]);

  const handleBatchCopy = useCallback(() => {
    if (!currentImage || currentWatermarks.length === 0) {
      toast.error('Add watermarks first');
      return;
    }

    setImageWatermarks(prev => {
      const updated = new Map(prev);
      images.forEach(img => {
        if (img.id !== currentImage.id) {
          const copiedWatermarks = currentWatermarks.map(wm => ({ ...wm }));
          updated.set(img.id, copiedWatermarks);
        }
      });
      return updated;
    });

    toast.success(`Watermarks copied to ${images.length - 1} images`);
  }, [currentImage, currentWatermarks, images]);

  const handleLoadWatermarkImage = useCallback(() => {
    watermarkImageInputRef.current?.click();
  }, []);

  const handleWatermarkImageChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !file.type.startsWith('image/') || selectedWatermarkIndex === null) return;

    const url = URL.createObjectURL(file);
    handleUpdateWatermark(selectedWatermarkIndex, {
      imageUrl: url,
      imageName: file.name,
    });
    
    e.target.value = '';
  }, [selectedWatermarkIndex, handleUpdateWatermark]);

  // Render a single image with watermarks to canvas
  const renderImageWithWatermarks = async (
    imageUrl: string,
    watermarks: WatermarkSettings[]
  ): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      
      img.onload = async () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext('2d');
        
        if (!ctx) {
          reject(new Error('Could not get canvas context'));
          return;
        }

        // Draw the base image
        ctx.drawImage(img, 0, 0);

        // Draw watermarks
        for (const watermark of watermarks) {
          const x = (watermark.x / 100) * canvas.width;
          const y = (watermark.y / 100) * canvas.height;

          ctx.save();
          ctx.globalAlpha = watermark.opacity;
          ctx.translate(x, y);
          ctx.rotate((watermark.rotation * Math.PI) / 180);

          if (watermark.type === 'text') {
            ctx.font = `${watermark.fontSize}px "${watermark.fontFamily}"`;
            ctx.fillStyle = watermark.color;
            ctx.textAlign = watermark.alignment;
            ctx.textBaseline = 'middle';
            ctx.fillText(watermark.text, 0, 0);
          } else if (watermark.type === 'image' && watermark.imageUrl) {
            // Load and draw watermark image
            const wmImg = new Image();
            wmImg.crossOrigin = 'anonymous';
            await new Promise<void>((res) => {
              wmImg.onload = () => {
                const scale = watermark.fontSize / 100;
                const w = wmImg.width * scale;
                const h = wmImg.height * scale;
                ctx.drawImage(wmImg, -w / 2, -h / 2, w, h);
                res();
              };
              wmImg.onerror = () => res();
              wmImg.src = watermark.imageUrl!;
            });
          }

          ctx.restore();
        }

        canvas.toBlob((blob) => {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error('Failed to create blob'));
          }
        }, 'image/png', 1.0);
      };

      img.onerror = () => reject(new Error('Failed to load image'));
      img.src = imageUrl;
    });
  };

  const handleExport = useCallback(async () => {
    if (images.length === 0) {
      toast.error('No images to export');
      return;
    }

    setIsExporting(true);
    const toastId = toast.loading('Preparing export...');

    try {
      const zip = new JSZip();
      const folder = zip.folder('watermarked-images');

      if (!folder) {
        throw new Error('Failed to create ZIP folder');
      }

      let processed = 0;
      const total = images.length;

      for (const image of images) {
        const watermarks = imageWatermarks.get(image.id) || [];
        
        toast.loading(`Processing ${processed + 1}/${total}: ${image.name}`, { id: toastId });

        try {
          const blob = await renderImageWithWatermarks(image.url, watermarks);
          
          // Get filename without extension and add _watermarked
          const nameParts = image.name.split('.');
          const ext = nameParts.pop() || 'png';
          const baseName = nameParts.join('.');
          const newName = `${baseName}_watermarked.png`;

          folder.file(newName, blob);
          processed++;
        } catch (err) {
          console.error(`Error processing ${image.name}:`, err);
          toast.error(`Failed to process ${image.name}`);
        }
      }

      toast.loading('Creating ZIP file...', { id: toastId });
      
      const zipBlob = await zip.generateAsync({ 
        type: 'blob',
        compression: 'DEFLATE',
        compressionOptions: { level: 6 }
      });

      const timestamp = new Date().toISOString().slice(0, 10);
      saveAs(zipBlob, `watermarked-images-${timestamp}.zip`);

      toast.success(`Exported ${processed} images!`, { id: toastId });
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Export failed', { id: toastId });
    } finally {
      setIsExporting(false);
    }
  }, [images, imageWatermarks]);

  return (
    <div className="h-screen flex flex-col bg-background p-4 gap-4">
      {/* Header */}
      <header className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
          <Droplet className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-xl font-semibold text-foreground">Watermark Studio</h1>
          <p className="text-xs text-muted-foreground">Add watermarks to your images</p>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex gap-4 min-h-0">
        {/* Canvas */}
        <div className="flex-1 flex flex-col gap-4 min-w-0">
          <ImageCanvas
            ref={canvasRef}
            imageUrl={currentImage?.url || null}
            watermarks={currentWatermarks}
            onWatermarkUpdate={handleUpdateWatermark}
            selectedWatermarkIndex={selectedWatermarkIndex}
            onSelectWatermark={setSelectedWatermarkIndex}
          />
          
          <ImageNavigation
            images={images}
            currentIndex={currentIndex}
            onNavigate={handleNavigate}
            onLoadFolder={handleLoadFolder}
            onLoadImage={handleLoadImage}
            onExport={handleExport}
            isExporting={isExporting}
          />
        </div>

        {/* Control Panel */}
        <ControlPanel
          watermarks={currentWatermarks}
          selectedIndex={selectedWatermarkIndex}
          onUpdate={handleUpdateWatermark}
          onAdd={handleAddWatermark}
          onDelete={handleDeleteWatermark}
          onSelect={setSelectedWatermarkIndex}
          onBatchCopy={handleBatchCopy}
          onLoadWatermarkImage={handleLoadWatermarkImage}
          customFonts={customFonts}
          fontsLoading={fontsLoading}
        />
      </div>

      {/* Hidden Inputs */}
      <input
        ref={folderInputRef}
        type="file"
        multiple
        accept="image/*"
        onChange={handleFolderChange}
        className="hidden"
        {...({ webkitdirectory: '', directory: '' } as React.InputHTMLAttributes<HTMLInputElement>)}
      />
      <input
        ref={imageInputRef}
        type="file"
        multiple
        accept="image/*"
        onChange={handleImageChange}
        className="hidden"
      />
      <input
        ref={watermarkImageInputRef}
        type="file"
        accept="image/*"
        onChange={handleWatermarkImageChange}
        className="hidden"
      />
    </div>
  );
};
