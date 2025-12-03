export interface ImageFile {
  id: string;
  file: File;
  url: string;
  name: string;
}

export interface WatermarkSettings {
  type: 'text' | 'image';
  text: string;
  fontFamily: string;
  fontSize: number;
  color: string;
  opacity: number;
  rotation: number;
  x: number;
  y: number;
  alignment: 'left' | 'center' | 'right';
  imageUrl?: string;
  imageName?: string;
}

export interface ImageWatermark {
  imageId: string;
  watermarks: WatermarkSettings[];
}

export interface FontInfo {
  name: string;
  family: string;
  file: string;
}

// System fonts (always available)
export const SYSTEM_FONTS: FontInfo[] = [
  { name: 'Inter', family: 'Inter', file: '' },
  { name: 'Arial', family: 'Arial', file: '' },
  { name: 'Georgia', family: 'Georgia', file: '' },
  { name: 'Times New Roman', family: 'Times New Roman', file: '' },
  { name: 'Courier New', family: 'Courier New', file: '' },
  { name: 'Verdana', family: 'Verdana', file: '' },
];

export const DEFAULT_WATERMARK: WatermarkSettings = {
  type: 'text',
  text: 'Watermark',
  fontFamily: 'Inter',
  fontSize: 48,
  color: '#ffffff',
  opacity: 0.7,
  rotation: 0,
  x: 50,
  y: 50,
  alignment: 'center',
};
