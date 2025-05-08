import logging
from google import genai # 사용자 제공 예시처럼 from google import genai 사용
# from google.generativeai import types as genai_types # genai.types 사용 시도, 없으면 아래에서 처리
from PIL import Image as PIL_Image
from io import BytesIO
from typing import Optional

from configs.settings import load_config

class ImageGenerator:
    """Google AI (genai.Client, 사용자 제공 예시)를 사용하여 이미지를 생성하는 클래스"""

    def __init__(self, image_model_name: str = "imagen-3.0-generate-002"):
        """
        ImageGenerator 초기화 (사용자 제공 genai.Client 예시 기반)
        Args:
            image_model_name (str): 사용할 Imagen 모델 이름. (예: "imagen-3.0-generate-002")
        """
        self.config = load_config()
        self.ai_config = self.config.get('ai', {})
        self.api_key = self.ai_config.get('api_key')
        
        if not self.api_key:
            logging.error("ImageGenerator: AI API 키가 설정 파일에 없습니다 (ai.api_key).")
            self.client = None
            self.image_model_name = None
            return

        self.image_model_name = image_model_name
        try:
            self.client = genai.Client(api_key=self.api_key)
            logging.info(f"ImageGenerator: genai.Client (사용자 예시 스타일) 초기화 완료. 사용할 모델: {self.image_model_name}")
        except AttributeError as ae:
            logging.error(f"ImageGenerator: 'genai.Client'를 찾을 수 없습니다. ({ae}). 'google.generativeai'와 다른 'google.genai' 모듈이 필요할 수 있습니다.", exc_info=True)
            self.client = None
        except Exception as e:
            logging.error(f"ImageGenerator: genai.Client (사용자 예시 스타일) 초기화 실패: {e}", exc_info=True)
            self.client = None

    def generate_halftone_image(self, subject_prompt: str, output_image_path: str) -> bool:
        """
        주어진 텍스트 기반으로 하프톤 이미지를 생성 (genai.Client, 사용자 예시 스타일).
        """
        if not self.client or not self.image_model_name:
            logging.error("ImageGenerator: genai.Client 또는 이미지 모델 이름이 초기화되지 않았습니다.")
            return False

        try:
            logging.info(f"ImageGenerator: genai.Client ({self.image_model_name}) 이미지 생성 시작.")

            background_color_hex = "#3100FF"
            background_color_rgb_description = "vibrant blue (RGB 49, 0, 255)" # 기존 설명 유지
            full_prompt = (
                f"Generate a halftone image for a post, focusing on clearly recognizable objects that represent the main keywords of the theme: '{subject_prompt}'. "
                f"The image must be in a distinct halftone style. The main subject/objects should be in black and white. "
                f"The background must be a solid color: {background_color_hex} ({background_color_rgb_description}). "
                f"The image must contain absolutely no text, letters, or numbers."
            ) # Prompt changed to English to emphasize halftone style and other requirements.
            logging.debug(f"genai.Client image generation prompt:\n{full_prompt}")

            genai_types_module = None
            try:
                # 먼저 google.genai.types 시도
                from google.genai import types as google_genai_types
                genai_types_module = google_genai_types
                logging.debug("Using google.genai.types")
            except (ImportError, AttributeError):
                try:
                    # 실패 시 google.generativeai.types 시도
                    from google.generativeai import types as google_generativeai_types
                    genai_types_module = google_generativeai_types
                    logging.debug("Using google.generativeai.types as fallback for genai.types")
                except (ImportError, AttributeError):
                    logging.error("'types' 모듈을 'google.genai' 또는 'google.generativeai'에서 찾을 수 없습니다.")
                    return False
            
            img_config_obj = None
            try:
                img_config_obj = genai_types_module.GenerateImagesConfig(number_of_images=1)
            except AttributeError:
                logging.warning(f"'{genai_types_module.__name__}.GenerateImagesConfig'를 찾을 수 없습니다. config 없이 호출합니다.")
            except TypeError as te:
                logging.warning(f"'{genai_types_module.__name__}.GenerateImagesConfig' 생성 실패 ({te}). config 없이 호출합니다.")

            if img_config_obj:
                response = self.client.models.generate_images(
                    model=self.image_model_name,
                    prompt=full_prompt,
                    config=img_config_obj
                )
            else:
                # GenerateImagesConfig 사용 불가 시, number_of_images 직접 전달 시도 (API가 지원해야 함)
                # 또는 다른 필수 파라미터가 있다면 추가 필요
                response = self.client.models.generate_images(
                    model=self.image_model_name,
                    prompt=full_prompt,
                    # 예시에서는 config에 number_of_images가 있었으므로, 직접 파라미터로 시도
                    number_of_images=1 
                )

            if not response or not hasattr(response, 'generated_images') or not response.generated_images:
                logging.error("genai.Client: 모델에서 이미지를 생성하지 못했거나 응답 형식이 올바르지 않습니다.")
                if response: logging.debug(f"실패 시 전체 응답: {response}")
                return False

            generated_image_data = response.generated_images[0].image.image_bytes

            if not generated_image_data:
                logging.error("genai.Client: 생성된 이미지에서 바이트 데이터를 가져올 수 없습니다.")
                return False
            
            logging.info(f"genai.Client: 이미지 바이트 데이터 수신 (크기: {len(generated_image_data)} bytes)")

            initial_image = PIL_Image.open(BytesIO(generated_image_data)).convert("RGBA")
            
            processed_image_data = []
            target_rgb = (49, 0, 255)
            tolerance = 45

            for item in initial_image.getdata():
                distance = abs(item[0] - target_rgb[0]) + \
                           abs(item[1] - target_rgb[1]) + \
                           abs(item[2] - target_rgb[2])
                
                if distance < tolerance:
                    processed_image_data.append((item[0], item[1], item[2], 0))
                else:
                    processed_image_data.append(item)
            
            initial_image.putdata(processed_image_data)
            
            if not output_image_path.lower().endswith(".png"):
                logging.warning(f"출력 파일 경로 '{output_image_path}'가 .png로 끝나지 않습니다.")

            initial_image.save(output_image_path, "PNG")
            logging.info(f"genai.Client (사용자 예시) Imagen 하프톤 이미지 저장 완료: {output_image_path}")
            return True

        except AttributeError as ae:
            logging.error(f"genai.Client API 호출 중 속성 오류 ({self.image_model_name}): {ae}. 'models.generate_images' 또는 'GenerateImagesConfig' 관련 문제일 수 있습니다.", exc_info=True)
            return False
        except Exception as e:
            logging.error(f"genai.Client 이미지 생성 중 예상치 못한 오류 ({self.image_model_name}): {e}", exc_info=True)
            return False
