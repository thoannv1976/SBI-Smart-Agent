# -*- coding: utf-8 -*-
"""Tổng hợp dữ liệu hỏi-đáp chương trình SBI (FTU) -> JSONL chuẩn để train AI Agent."""
import json, os

# Ghi dữ liệu ra chính thư mục chứa script này (thư mục data/ của dự án).
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

SYSTEM_PROMPT = (
    "Bạn là một trợ lý ảo tư vấn tuyển sinh AI của Trường Đại học Ngoại thương (FTU), "
    "chuyên tư vấn về chương trình đào tạo Thương mại số thông minh & Đổi mới kinh doanh "
    "(Smart Digital Commerce and Business Innovation - SBI), thuộc ngành Thương mại điện tử "
    "(Mã ngành: 7340122). Nhiệm vụ của bạn là trả lời các câu hỏi của học sinh, phụ huynh về "
    "chương trình học, cơ hội việc làm, các môn học, và thông tin chung về chương trình SBI "
    "dựa trên thông tin được cung cấp. Hãy trả lời một cách thân thiện, chuyên nghiệp, rõ ràng "
    "và súc tích. Nếu không biết câu trả lời, hãy hướng dẫn họ liên hệ trực tiếp với Khoa Quản "
    "trị Kinh doanh, Trường Đại học Ngoại thương."
)

# (category, question, answer) — gộp & loại trùng, chỉ dùng dữ liệu gốc trong 3 file.
QA = [
    # ===== THÔNG TIN CHUNG =====
    ("thong_tin_chung",
     "Chương trình SBI là gì và bằng cấp nhận được sau khi tốt nghiệp là gì?",
     "Chương trình Thương mại số thông minh & Đổi mới kinh doanh (Smart Digital Commerce and Business Innovation - SBI) là chương trình đào tạo trình độ đại học định hướng nghề nghiệp quốc tế, thuộc ngành Thương mại điện tử (mã ngành 7340122). Sau khi hoàn thành 131 tín chỉ, sinh viên sẽ được cấp bằng Cử nhân ngành Thương mại điện tử."),
    ("thong_tin_chung",
     "Chương trình học trong bao lâu và sử dụng ngôn ngữ gì?",
     "Thời gian đào tạo chính quy là 04 năm, tương đương 8 học kỳ. Chương trình được giảng dạy bằng tiếng Anh và tiếng Việt."),
    ("thong_tin_chung",
     "Điểm khác biệt của chương trình SBI so với các chương trình Thương mại điện tử truyền thống là gì?",
     "Chương trình SBI không chỉ tập trung vào thương mại điện tử cơ bản mà còn khai thác sâu về thương mại số thông minh, kinh doanh số, AI trong thương mại điện tử và phân tích dữ liệu lớn. Đặc biệt, chương trình áp dụng mô hình đồng giảng dạy (co-teaching) 3 bên gồm: Trường đại học (FTU), giảng viên nước ngoài và chuyên gia từ doanh nghiệp/cơ quan quản lý nhà nước."),
    ("thong_tin_chung",
     "Triết lý đào tạo và slogan của chương trình SBI là gì?",
     "Triết lý đào tạo: \"Giáo dục hướng đến phát triển tư duy Thương mại số thông minh & Đổi mới kinh doanh, ứng dụng đổi mới sáng tạo và công nghệ tiên tiến nhằm giải quyết các thách thức thực tiễn, nuôi dưỡng tính trung thực và tinh thần trách nhiệm trong kinh doanh hiện đại.\" Chương trình dựa trên 3 trụ cột: (1) E-commerce – Thương mại điện tử; (2) Digital Commerce – Thương mại số, Kinh doanh số, Kinh doanh thông minh; (3) Công nghệ số và Đổi mới kinh doanh. Slogan: \"Kết nối công nghệ - Khơi nguồn đổi mới - Kiến tạo giá trị bền vững\" (Connecting technology - inspiring innovation - creating sustainable values)."),
    ("thong_tin_chung",
     "Mục tiêu đào tạo của chương trình SBI là gì?",
     "Chương trình đào tạo nguồn nhân lực chất lượng cao trong lĩnh vực thương mại số thông minh định hướng nghề nghiệp quốc tế. Sinh viên tốt nghiệp có năng lực tư duy phản biện, đổi mới sáng tạo, ứng dụng công nghệ số và kỹ năng nghề nghiệp để triển khai các dự án thương mại điện tử, kinh doanh số, kinh doanh thông minh; có thể đảm nhận các vị trí chuyên viên, nhà quản lý, chuyên gia tư vấn hoạch định chính sách về thương mại điện tử, thương mại số, kinh doanh số và kinh doanh thông minh."),
    ("thong_tin_chung",
     "Đơn vị nào phụ trách chuyên môn chương trình SBI?",
     "Khoa Quản trị Kinh doanh, Trường Đại học Ngoại thương (FTU) là đơn vị phụ trách chuyên môn. Khoa được thành lập năm 1999, gồm 5 bộ môn, với đội ngũ 58 giảng viên cơ hữu (trong đó có 7 PGS, 29 Tiến sĩ và 18 Thạc sĩ), phần lớn được đào tạo tại Mỹ, Anh, Úc, Nhật Bản…"),

    # ===== TUYỂN SINH =====
    ("tuyen_sinh",
     "Chỉ tiêu tuyển sinh của chương trình là bao nhiêu?",
     "Chương trình dự kiến tuyển sinh 50 sinh viên/khóa, nằm trong tổng chỉ tiêu đào tạo hàng năm của Trường Đại học Ngoại thương và xét tuyển theo hệ thống tuyển sinh chung của trường."),

    # ===== CHƯƠNG TRÌNH ĐÀO TẠO =====
    ("chuong_trinh_dao_tao",
     "Cấu trúc 131 tín chỉ của chương trình SBI được phân bổ như thế nào?",
     "Chương trình gồm 131 tín chỉ (không bao gồm Giáo dục thể chất và Giáo dục quốc phòng), chia thành 4 khối: (1) Kiến thức giáo dục đại cương: 23 tín chỉ (17,5%); (2) Kiến thức giáo dục chuyên nghiệp: 84 tín chỉ (64,1%) — gồm cơ sở khối ngành KT-QTKD 33 tín chỉ và kiến thức ngành/chuyên ngành TMĐT 51 tín chỉ (trong đó tự chọn chuyên sâu 12 tín chỉ); (3) Học phần thực hành nghề nghiệp: 15 tín chỉ (11,5%); (4) Học phần tốt nghiệp - Dự án sáng tạo: 9 tín chỉ (6,9%)."),
    ("chuong_trinh_dao_tao",
     "Kế hoạch đào tạo 4 năm SBI phân bổ môn học qua từng năm thế nào?",
     "Chương trình phân bổ trong 4 năm (8 học kỳ), gắn với lộ trình phát triển theo chủ đề từng năm: Năm 1 (IceBreakers) hoàn thành khối đại cương, tiếp cận môn cơ sở ngành (Toán, Kinh tế học, Tiếng Anh chuyên ngành) và học phần thực hành SBI1 định hướng nghề nghiệp. Năm 2 (Explorers) mở rộng môn cơ sở ngành (Quản trị, Marketing) và môn ngành cốt lõi (TMĐT căn bản, Cơ sở dữ liệu trong TMĐT) cùng học phần SBI2. Năm 3 (Innovators) học các học phần chuyên ngành sâu theo 1 trong 2 hướng chuyên sâu, cùng SBI3. Năm 4 (Ambassadors): kỳ 7 hoàn thiện kiến thức bậc cao và SBI4; kỳ 8 dành trọn cho Đề án tốt nghiệp SBI5 (9 tín chỉ) tại doanh nghiệp."),
    ("chuong_trinh_dao_tao",
     "Các môn học tiêu biểu của chương trình SBI gồm những gì?",
     "Khối đại cương: Triết học Mác-Lênin, Kinh tế chính trị, Toán xác suất thống kê, Pháp luật đại cương, Mạng máy tính và truyền thông, Tư duy thiết kế & đổi mới sáng tạo, Phương pháp nghiên cứu. Khối cơ sở ngành: Kinh tế vi mô, Kinh tế vĩ mô, Quản trị học, Nguyên lý thống kê, Marketing căn bản, Nguyên lý kế toán, Tiếng Anh chuyên ngành (1-5). Khối ngành TMĐT bắt buộc: Thương mại điện tử căn bản, Cơ sở dữ liệu trong TMĐT, Hệ thống thông tin quản lý, Pháp luật TMĐT, Chính phủ số và chuyển đổi số trong kinh doanh, Chiến lược kinh doanh số, Quản trị marketing số, Quản trị thương hiệu số, An toàn thông tin và bảo mật trong TMĐT, Thương mại số và Kinh doanh thông minh."),
    ("chuong_trinh_dao_tao",
     "Các học phần thực hành nghề nghiệp (SBI1-SBI5) gồm những gì?",
     "Khối thực hành nghề nghiệp (15 tín chỉ) gồm: SBI1 - Phát triển kỹ năng và định hướng nghề nghiệp; SBI2 - Quản trị Website và cửa hàng trực tuyến trong thương mại số; SBI3 - Thanh toán điện tử và giao dịch tài chính ngân hàng điện tử; SBI4 - Kinh doanh thông minh và Đổi mới kinh doanh trên các nền tảng số. Học phần tốt nghiệp là SBI5 - Đề án tốt nghiệp (Dự án sáng tạo quốc tế), 9 tín chỉ."),
    ("chuong_trinh_dao_tao",
     "Các học phần AI trong chương trình gồm những nội dung gì?",
     "Chương trình trang bị kiến thức về AI qua 2 môn chính: (1) Công nghệ số và ứng dụng trí tuệ nhân tạo (TINE210) - phân tích bản chất, nguyên lý, xu hướng và ứng dụng của AI, điện toán đám mây, dữ liệu lớn (Big Data), IoT và Blockchain, cùng tác động tới kinh doanh, marketing, chuỗi cung ứng, thanh toán và đổi mới mô hình kinh doanh; (2) AI trong Thương mại điện tử (SBIE201) - tập trung vào lịch sử và bản chất AI, học máy (Machine Learning) và học sâu (Deep Learning), xử lý ngôn ngữ tự nhiên (NLP) và chatbot, hệ thống gợi ý, robot và tự động hóa quy trình (RPA), cùng các vấn đề đạo đức, pháp lý và chiến lược triển khai AI."),
    ("chuong_trinh_dao_tao",
     "Phương pháp giảng dạy của chương trình SBI là gì?",
     "Chương trình áp dụng các phương pháp hiện đại: lấy người học làm trung tâm (learner-centered), Flipped Classroom (lớp học đảo ngược), Simulation-based Learning (học qua mô phỏng), Project-based Learning (học tập theo dự án) và mô hình Co-teaching 3 bên (giảng viên FTU, giảng viên nước ngoài, chuyên gia doanh nghiệp)."),

    # ===== CHUYÊN SÂU =====
    ("chuyen_sau",
     "Chương trình có những hướng chuyên sâu nào để lựa chọn?",
     "Chương trình có 2 hướng chuyên sâu để sinh viên tự chọn: (1) Đổi mới mô hình thương mại số thông minh / Quản trị đổi mới trong Thương mại số (Innovation Management in Digital Commerce) và (2) Thương mại điện tử xuyên biên giới (Cross-Border E-Commerce). Với mỗi chuyên sâu, sinh viên chọn học 4 trong số các học phần tương ứng (12 tín chỉ)."),
    ("chuyen_sau",
     "Chi tiết hai hướng chuyên sâu của SBI khác nhau như thế nào?",
     "Chuyên sâu 1 - Quản trị đổi mới trong Thương mại số: tập trung ứng dụng công nghệ tiên tiến (AI, Học máy, Blockchain) và khai thác dữ liệu để sáng tạo, cải tiến mô hình kinh doanh, sản phẩm và dịch vụ; học các môn như Khởi nghiệp và Đổi mới sáng tạo, Ứng dụng AI trong đổi mới sáng tạo, Kinh doanh số và vốn hoá dữ liệu, Mô hình kinh doanh nền tảng, Quản trị sản phẩm trong môi trường số, Kinh doanh thông minh. Chuyên sâu 2 - Thương mại điện tử xuyên biên giới: trang bị chiến lược, nghiệp vụ và kỹ năng vận hành hệ thống TMĐT quy mô quốc tế; học các môn như Quản lý chuỗi cung ứng TMĐT xuyên biên giới, Logistics toàn cầu, Thanh toán quốc tế, Luật và chính sách TMĐT quốc tế, Quản trị sàn TMĐT quốc tế và kênh bán đa nền tảng. Khác biệt cốt lõi: một bên khai thác công nghệ và dữ liệu để tạo mô hình kinh doanh đột phá, bên còn lại kết nối thị trường và tối ưu chuỗi vận hành/giao dịch toàn cầu."),
    ("chuyen_sau",
     "Các môn học tiêu biểu của chuyên sâu TMĐT xuyên biên giới là gì?",
     "Sinh viên chọn 4 học phần, gồm các môn tiêu biểu: Quản lý chuỗi cung ứng TMĐT xuyên biên giới / Logistics và chuỗi cung ứng toàn cầu (tích hợp IoT, Blockchain, AI, tự động hóa cho vận chuyển, kho vận, hải quan, hoàn tất đơn hàng quốc tế); Thương mại điện tử đa kênh tích hợp / Chiến lược đa kênh (omni-channel); Dữ liệu lớn trong TMĐT xuyên biên giới; Thiết kế giao diện và trải nghiệm người dùng xuyên biên giới (UX); Thanh toán quốc tế trong TMĐT; Luật pháp và chính sách TMĐT quốc tế; Chiến lược kinh doanh TMĐT xuyên biên giới; Quản trị sàn TMĐT quốc tế và kênh bán đa nền tảng."),
    ("chuyen_sau",
     "Lộ trình nghề nghiệp giữa hai chuyên sâu khác nhau ra sao?",
     "Hướng Đổi mới kinh doanh: ngay sau tốt nghiệp làm Nhân viên phân tích dữ liệu trong thương mại số hoặc Nhân viên quản lý sản phẩm AI; sau 3-5 năm thăng tiến lên Tư vấn chiến lược số hoặc Quản lý đổi mới sáng tạo. Hướng TMĐT xuyên biên giới: khởi đầu làm Quản trị viên hoạt động TMĐT xuyên biên giới hoặc Chuyên viên chuỗi cung ứng/logistics toàn cầu; sau 3-5 năm vươn lên Quản lý Marketing số quốc tế hoặc Quản trị và vận hành sàn TMĐT quốc tế."),

    # ===== THỰC HÀNH & DỰ ÁN =====
    ("thuc_hanh_du_an",
     "Trong quá trình học, sinh viên có được thực hành thực tế không?",
     "Có. Chương trình chú trọng học tập dựa trên dự án (Project-based Learning). Sinh viên thực hiện 3 dự án kinh doanh lớn vào năm 2, năm 3 và năm 4 (thiết lập mô hình kinh doanh số, xây dựng website TMĐT, áp dụng AI/Big Data cải tiến doanh nghiệp) và có thời gian thực hành trực tiếp tại các doanh nghiệp."),
    ("thuc_hanh_du_an",
     "Lộ trình học 3 dự án kinh doanh cụ thể là gì?",
     "Năm 2 - Dự án phát triển mô hình kinh doanh số cơ bản: nghiên cứu thị trường, phân tích hành vi khách hàng và xây dựng chiến lược tiếp thị số cho một sản phẩm/dịch vụ. Năm 3 - Dự án phát triển và triển khai nền tảng TMĐT: làm việc nhóm xây dựng website bán hàng, tích hợp hệ thống thanh toán điện tử và chạy các chiến dịch tiếp thị số thực tế. Năm 4 - Dự án đề xuất giải pháp cải tiến cho doanh nghiệp thực tiễn: làm việc trực tiếp với doanh nghiệp đối tác, phân tích dữ liệu kinh doanh và ứng dụng công nghệ tiên tiến (AI, Big Data, Blockchain) để đưa ra giải pháp cải tiến."),
    ("thuc_hanh_du_an",
     "Dự án năm 2 nghiên cứu và phát triển chiến lược tiếp thị số như thế nào?",
     "Trong năm 2, qua Dự án phát triển mô hình kinh doanh số cơ bản, sinh viên: nghiên cứu thị trường và phân tích khách hàng trên một sản phẩm/dịch vụ cụ thể; xây dựng kế hoạch tiếp thị trực tuyến dựa trên phân tích dữ liệu; làm việc nhóm và giải quyết tình huống thực tế qua bài tập nhóm, thuyết trình bảo vệ quan điểm. Dự án gắn liền với môn Quản trị marketing số (Digital Marketing Management)."),
    ("thuc_hanh_du_an",
     "Dự án năm 3 về triển khai nền tảng TMĐT gồm những nhiệm vụ cụ thể nào?",
     "Sinh viên làm việc theo nhóm phát triển dự án từ ý tưởng đến hiện thực hóa, với các nhiệm vụ: (1) Xây dựng website bán hàng - thiết kế, phát triển và quản trị một trang web TMĐT; (2) Tích hợp hệ thống thanh toán điện tử - kết nối các cổng thanh toán trực tuyến để xử lý giao dịch; (3) Triển khai các chiến dịch tiếp thị số - vận hành marketing trực tuyến để quảng bá sản phẩm/dịch vụ."),
    ("thuc_hanh_du_an",
     "Sinh viên năm cuối giải quyết các bài toán thực tế nào cho doanh nghiệp?",
     "Vào năm 4, qua Dự án nghiên cứu và đề xuất giải pháp cải tiến và học phần SBI5, sinh viên hợp tác trực tiếp với doanh nghiệp đối tác để: tìm hiểu và tháo gỡ các vấn đề phức tạp của doanh nghiệp; phân tích dữ liệu kinh doanh thực tế; ứng dụng công nghệ tiên tiến (AI, Big Data, Blockchain) vào cải tiến quy trình/sản phẩm; thiết kế giải pháp đổi mới sáng tạo. Quá trình này đòi hỏi tích hợp năng lực nghiên cứu độc lập, quản trị dự án, tư duy chiến lược và làm việc nhóm."),
    ("thuc_hanh_du_an",
     "Dự án tốt nghiệp SBIMAS/SBI5 được thực hiện như thế nào?",
     "SBI5 (mã học phần SBIE400) - \"Dự án sáng tạo quốc tế trong TMĐT\" là học phần kết tinh ứng dụng cao nhất của chương trình, với 9 tín chỉ (bao gồm 90 giờ trên lớp, 90 giờ thực tế và 270 giờ tự học). Sinh viên dành học kỳ 8 hoàn thành khóa luận/đề án trực tiếp tại cơ sở thực tế, làm việc cùng doanh nghiệp đối tác để giải quyết một vấn đề thực tiễn phức tạp, ứng dụng AI/Big Data/Blockchain và tích hợp toàn bộ kiến thức chuyên môn, kỹ năng số, tư duy đổi mới sáng tạo. Dự án rèn luyện năng lực nghiên cứu độc lập, quản trị dự án, trình bày chuyên nghiệp, tư duy chiến lược và kỹ năng phản biện."),
    ("thuc_hanh_du_an",
     "Các phần mềm mô phỏng kinh doanh được sử dụng ra sao?",
     "Chương trình tích hợp phương pháp Học tập qua mô phỏng (Simulation-based Learning). Giảng viên sử dụng các phần mềm nổi tiếng như Capsim, Cesim hoặc các mô hình mô phỏng chuỗi cung ứng để tạo tình huống giả định sát thực tế. Sinh viên trải nghiệm điều hành doanh nghiệp trong môi trường ảo, tự đưa ra quyết định kinh doanh chiến lược và thấy ngay tác động của các quyết định đó trước khi áp dụng vào thị trường thực tế."),
    ("thuc_hanh_du_an",
     "Sinh viên có được thực tập tại doanh nghiệp đối tác không?",
     "Có. Sinh viên hoàn toàn có cơ hội thực tập và làm việc trực tiếp tại doanh nghiệp đối tác: 1 học kỳ (kỳ 8) dành riêng để hoàn thành khóa luận/đề án tốt nghiệp tại cơ sở thực tế; năm 4 hợp tác làm dự án với doanh nghiệp đối tác; có cơ hội thực tập và làm việc quốc tế qua mạng lưới hợp tác toàn cầu; và tương tác với doanh nghiệp ngay trong quá trình học qua mô hình coaching, mentoring, co-teaching."),
    ("thuc_hanh_du_an",
     "Hoạt động ngoại khóa IceBreakers của sinh viên năm nhất là gì?",
     "IceBreakers là chuỗi hoạt động ngoại khoá kết hợp với chương trình đào tạo dành cho sinh viên năm nhất, gắn với khối kiến thức đại cương và học phần thực hành SBI1. Qua đó sinh viên: phát triển toàn diện kỹ năng học tập, kỹ năng nghề nghiệp và tư duy chiến lược; được định hướng nghề nghiệp theo xu thế kinh tế số; trang bị nền tảng về chuẩn năng lực, hành trang khởi đầu; và học cách tự xây dựng kế hoạch học tập cá nhân hiệu quả cho 4 năm đại học."),
    ("thuc_hanh_du_an",
     "Lộ trình đào tạo SBI qua 4 năm (IceBreakers, Explorers, Innovators, Ambassadors) diễn ra thế nào?",
     "Lộ trình 4 năm/8 học kỳ gắn với chủ đề phát triển từng năm: Năm 1 - IceBreakers (Khởi động & Định hướng): học đại cương, nền tảng kinh tế-quản trị, trọng tâm là SBI1. Năm 2 - Explorers (Khám phá nền tảng TMĐT): học môn ngành cốt lõi và thực hiện Dự án mô hình kinh doanh số cơ bản. Năm 3 - Innovators (Đổi mới sáng tạo & Ứng dụng): học chuyên sâu theo 2 hướng, AI và Học máy, triển khai Dự án nền tảng TMĐT (SBI2, SBI3). Năm 4 - Ambassadors (Kiến tạo giá trị & Trải nghiệm thực tế): SBI4 và học kỳ 8 thực hiện Đề án tốt nghiệp SBI5 tại doanh nghiệp."),

    # ===== CÔNG NGHỆ & CÔNG CỤ =====
    ("cong_nghe_cong_cu",
     "Chương trình SBI đào tạo những kỹ năng công nghệ cốt lõi nào?",
     "Chương trình trang bị 3 năng lực cốt lõi (phân tích dữ liệu phục vụ ra quyết định, triển khai chuyển đổi số, phát triển giải pháp kinh doanh sáng tạo) và đào tạo 5 nhóm kỹ năng công nghệ để đạt chuẩn bậc 6/8 Khung năng lực số: (1) Phân tích dữ liệu và Big Data (Power BI, Tableau, Python, R, Google Analytics); (2) Ứng dụng AI và Học máy (tối ưu vận hành, tự động hóa dịch vụ, đổi mới sản phẩm); (3) Vận hành hệ thống và nền tảng TMĐT (Shopify, WooCommerce, ERP, CRM, SCM, omni-channel, thanh toán điện tử); (4) Công nghệ 4.0 tiên tiến (Blockchain, smart contract, DeFi, IoT, tự động hóa, điện toán đám mây); (5) Nền tảng CNTT và bảo mật (lập trình cơ bản, phát triển website, an toàn thông tin, an ninh mạng, bảo mật dữ liệu)."),
    ("cong_nghe_cong_cu",
     "Sinh viên được học các công cụ phân tích dữ liệu nào?",
     "Chương trình chú trọng thực hành trên các phần mềm phân tích, thống kê và trí tuệ doanh nghiệp (BI) hiện đại: Power BI (công cụ chính để trực quan hóa dữ liệu, xây dashboard tương tác); SPSS (phân tích thống kê dữ liệu); Tableau và Google Data Studio (BI trực quan hóa); Google Analytics (phân tích dữ liệu hành vi người dùng trên nền tảng TMĐT)."),
    ("cong_nghe_cong_cu",
     "Sinh viên SBI được thực hành trên những phần mềm công nghệ nào?",
     "Sinh viên thực hành trên nhiều nhóm phần mềm: (1) Phân tích dữ liệu và lập trình: Power BI, Tableau, Google Analytics, Python, R; (2) Nền tảng TMĐT và quản trị doanh nghiệp: Shopify, WooCommerce, hệ thống ERP, CRM, SCM, các nền tảng omni-channel và thanh toán điện tử; (3) Mô phỏng kinh doanh: Capsim, Cesim và mô hình mô phỏng chuỗi cung ứng; (4) Quản lý dự án và làm việc nhóm: Trello, Asana, cùng các phần mềm Zoom, Microsoft Teams, Google Classroom, Moodle."),
    ("cong_nghe_cong_cu",
     "Trường có trang bị đủ máy móc, phần mềm phục vụ ngành học công nghệ này không?",
     "Có. Trường có hệ thống cơ sở vật chất hiện đại gồm các phòng lab, phòng khai thác mạng và phòng vi tính tốc độ cao. Sinh viên được sử dụng phần mềm mô phỏng quản trị kinh doanh (Capsim, Cesim) và thực hành trên các phần mềm phân tích dữ liệu thực tế như Google Analytics, Tableau, Power BI, SPSS, Python, R."),

    # ===== CƠ HỘI VIỆC LÀM =====
    ("co_hoi_viec_lam",
     "Cơ hội việc làm sau khi ra trường như thế nào?",
     "Cơ hội việc làm rộng mở, tập trung vào 4 nhóm chính: (1) Chiến lược & Quản trị: Chuyên viên phân tích kinh doanh số, nghiên cứu thị trường số; (2) Công nghệ 4.0 & Phát triển hệ thống: Chuyên viên AI/ML trong TMĐT, chuyên viên tích hợp hệ thống; (3) Nghiệp vụ TMĐT: Chuyên viên Marketing số, Quản trị phân phối đa kênh (Omni-channel), Logistics số, Kinh doanh xuyên biên giới; (4) Đổi mới kinh doanh: Chuyên viên ứng dụng AI đổi mới sản phẩm, phân tích dữ liệu dự báo."),
    ("co_hoi_viec_lam",
     "Các vị trí việc làm và lộ trình thăng tiến sau khi tốt nghiệp SBI là gì?",
     "Nghề nghiệp chia thành 4 nhóm với lộ trình thăng tiến sau 3-5 năm: Nhóm Chiến lược & Quản trị: từ Chuyên viên Phân tích Kinh doanh Số / Nghiên cứu Thị trường Số lên Giám đốc Chiến lược số và TMĐT, Giám đốc Chuyển đổi số, Giám đốc Điều hành TMĐT toàn cầu. Nhóm Công nghệ 4.0: từ Chuyên viên AI/ML, Tích hợp Hệ thống TMĐT lên Giám đốc Công nghệ 4.0, Giám đốc Hệ sinh thái nền tảng số. Nhóm Nghiệp vụ TMĐT: từ Chuyên viên Marketing số, Omni-channel, Logistics số, Kinh doanh xuyên biên giới lên Giám đốc Vận hành Thương mại Số Toàn diện. Nhóm Đổi mới Kinh doanh: từ Chuyên viên Ứng dụng AI / Phân tích Dữ liệu và Dự báo lên Giám đốc Chiến lược Dữ liệu và AI, Giám đốc Ứng dụng AI, Giám đốc Đổi mới Kinh doanh số."),
    ("co_hoi_viec_lam",
     "Ngoài doanh nghiệp, sinh viên tốt nghiệp SBI có thể làm những công việc nào khác?",
     "Sau khi tích lũy kinh nghiệm, sinh viên còn có thể đảm nhận: Giảng viên giảng dạy các môn liên quan đến TMĐT tại các cơ sở giáo dục đại học; Chuyên gia tư vấn về thương mại điện tử cho doanh nghiệp; Chuyên viên thương mại điện tử tại các cơ quan quản lý Nhà nước, đơn vị sự nghiệp của Nhà nước."),
    ("co_hoi_viec_lam",
     "Chương trình có giúp ích cho việc làm việc ở môi trường quốc tế không?",
     "Có, đây là chương trình định hướng nghề nghiệp quốc tế. Sinh viên được trau dồi 5 học phần tiếng Anh chuyên ngành (Giao tiếp kinh doanh, Thư tín thương mại, Đàm phán Hợp đồng, Diễn thuyết, Tiếng Anh Thương mại số), đảm bảo năng lực ngoại ngữ ở mức B2-C1 (tương đương Bậc 5/6 Khung năng lực ngoại ngữ Việt Nam) và kỹ năng giao tiếp chuyên nghiệp. Ngoài ra, chuyên sâu TMĐT xuyên biên giới trang bị kỹ năng bán hàng trên các nền tảng toàn cầu như Amazon, Alibaba."),

    # ===== GIẢNG VIÊN & ĐỐI TÁC =====
    ("giang_vien_doi_tac",
     "Ai sẽ là người trực tiếp giảng dạy sinh viên?",
     "Sinh viên học với đội ngũ giảng viên cơ hữu chất lượng cao của Khoa Quản trị Kinh doanh (phần lớn tốt nghiệp từ Mỹ, Anh, Úc, Nhật…). Nhờ mô hình đồng giảng dạy, sinh viên còn được học trực tiếp với giảng viên quốc tế và chuyên gia/nhà lãnh đạo từ các doanh nghiệp và cơ quan quản lý nhà nước."),
    ("giang_vien_doi_tac",
     "Mô hình đào tạo đồng giảng 3 bên hoạt động như thế nào?",
     "Mô hình Co-teaching 3 bên kết hợp giảng dạy trực tiếp từ ba nhóm: (1) Giảng viên FTU - cung cấp kiến thức nền tảng về lý thuyết và phương pháp; (2) Giảng viên nước ngoài - mang góc nhìn quốc tế và kinh nghiệm từ các nền kinh tế phát triển; (3) Chuyên gia từ doanh nghiệp và cơ quan quản lý - chia sẻ trường hợp thực tiễn, cập nhật quy định pháp luật và chính sách mới nhất. Mô hình giúp sinh viên tích lũy kiến thức đa chiều và tiếp xúc trực tiếp với doanh nghiệp ngay trên giảng đường."),
    ("giang_vien_doi_tac",
     "Vai trò của Doanh nghiệp và Nhà nước trong đào tạo SBI là gì?",
     "Chương trình có sự tham gia trực tiếp của 3 bên: Trường đại học, Doanh nghiệp và Cơ quan quản lý Nhà nước/Hiệp hội. Doanh nghiệp và cơ quan quản lý tham gia đồng giảng dạy (mang góc nhìn đa chiều, chia sẻ case study thực tiễn, cập nhật quy định pháp luật và chính sách mới); đồng thời tạo môi trường thực hành thực tiễn — đặc biệt trong năm 4, doanh nghiệp đóng vai trò \"đối tác\" để sinh viên nghiên cứu, tìm hiểu vấn đề và đề xuất giải pháp công nghệ cải tiến cho chính doanh nghiệp đó."),
    ("giang_vien_doi_tac",
     "Sinh viên sẽ được làm việc với các doanh nghiệp đối tác nào?",
     "Thông qua học tập theo dự án, mô phỏng doanh nghiệp ảo và mô hình đồng giảng, sinh viên được tiếp cận và làm việc với các doanh nghiệp/nền tảng tiêu biểu gồm: Shopee, FPTShop, VNPost, VNG, Gode, Alibaba và Amazon. Ngoài ra, chương trình còn kết nối với mạng lưới rộng lớn các doanh nghiệp, hiệp hội ngành nghề và cơ quan quản lý nhà nước trong và ngoài nước."),
    ("giang_vien_doi_tac",
     "Chương trình SBI có những đối tác trường đại học quốc tế nào?",
     "Chương trình có mạng lưới hợp tác chiến lược với hơn 350 trường đại học và tổ chức uy tín từ hơn 36 quốc gia và vùng lãnh thổ. Một số đối tác học thuật tiêu biểu: Đại học George Mason, Đại học Bang Colorado, Đại học Bang California – Fullerton (Hoa Kỳ); Đại học Northampton (Anh); Đại học Tohoku (Nhật Bản); Đại học Woosong (Hàn Quốc); Đại học Queensland (Úc); Đại học Ứng dụng Tây Bắc Thụy Sĩ (Thụy Sỹ)."),

    # ===== VỀ TRƯỜNG FTU & CƠ SỞ VẬT CHẤT =====
    ("ve_truong_ftu",
     "Trường Đại học Ngoại thương có những cơ sở đào tạo nào?",
     "Trường Đại học Ngoại thương có Trụ sở chính tại số 91 phố Chùa Láng, phường Láng Thượng, quận Đống Đa, TP. Hà Nội; Cơ sở II tại số 15 đường D5, quận Bình Thạnh, TP.HCM; và Cơ sở Quảng Ninh tại số 260 đường Bạch Đằng, phường Nam Khê, TP. Uông Bí, tỉnh Quảng Ninh."),
    ("ve_truong_ftu",
     "Sứ mạng và tầm nhìn của Trường Đại học Ngoại thương là gì?",
     "Sứ mạng: \"Phụng sự xã hội bằng sự xuất sắc trong giáo dục, sáng tạo và chuyển giao tri thức.\" Tầm nhìn: \"Trở thành đại học đổi mới sáng tạo, nằm trong nhóm các đại học hàng đầu châu Á.\" Giá trị cốt lõi: Sáng tạo và Xuất sắc; Trách nhiệm và Bản lĩnh; Đa dạng và Hòa hợp. Phương châm hành động: \"Khác biệt để dẫn đầu.\""),
    ("co_so_vat_chat",
     "Cơ sở vật chất và hạ tầng công nghệ phục vụ chương trình SBI gồm những gì?",
     "Trường có 85 phòng học (20-60m2), 2 hội trường lớn, 13 phòng họp đa phương tiện, 4 phòng lab, 6 phòng vi tính (mỗi phòng 30 máy tốc độ cao), 1 phòng khai thác mạng (trên 60 máy), 1 phòng đọc đa năng. Sinh viên thực hành trên các nền tảng TMĐT, hệ thống quản trị chuỗi cung ứng, ERP, CRM và công cụ phân tích dữ liệu như Power BI, Tableau, Python, R. Thư viện có trên 122.645 tư liệu cùng nhiều cơ sở dữ liệu điện tử (Emerald, SAGE, Springer, Statista, FiinPro-X...)."),
]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    # 1) JSONL chính (training/RAG)
    jsonl_path = os.path.join(OUT_DIR, "sbi_qa_dataset.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for i, (cat, q, a) in enumerate(QA, 1):
            rec = {
                "id": f"sbi-{i:03d}",
                "category": cat,
                "question": q.strip(),
                "answer": a.strip(),
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # 2) JSONL định dạng chat/messages (sẵn sàng fine-tune)
    chat_path = os.path.join(OUT_DIR, "sbi_qa_chat.jsonl")
    with open(chat_path, "w", encoding="utf-8") as f:
        for cat, q, a in QA:
            rec = {"messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": q.strip()},
                {"role": "assistant", "content": a.strip()},
            ]}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print("Records:", len(QA))
    print("Categories:", sorted(set(c for c, _, _ in QA)))
    # kiểm tra trùng câu hỏi
    qs = [q.strip().lower() for _, q, _ in QA]
    dups = set(x for x in qs if qs.count(x) > 1)
    print("Duplicate questions:", dups if dups else "none")
    print("Wrote:", jsonl_path)
    print("Wrote:", chat_path)


if __name__ == "__main__":
    main()
