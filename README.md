# AI-Assistant
An AI assistant that understands both image and text input, and provides intelligent text output.

# 开发手册（初版，欢迎大家修改补充 ^ ^）
定义4个文件：
1 frontend.html
一个前端展示界面，可以接受用户输入文字，上传图片。和输出文字结果。

2 backend_image_input.py
后端input图片调用gpt的接口。

3 backend_test_input.py
后端input文字调用gpt的接口。

4 backend_output.py
后端output文字结果的接口，这个接口统一接受步骤2和3的输出，统一处理后输出给步骤1的前端展示
