
DROP FUNCTION IF EXISTS check_bname;
DROP FUNCTION IF EXISTS check_author;
DROP FUNCTION IF EXISTS check_pub;
DROP FUNCTION IF EXISTS check_pubtime;
DROP PROCEDURE IF EXISTS manage_book_stock;

-- 创建检查书名的函数
DELIMITER //

CREATE FUNCTION check_bname(p_isbn VARCHAR(50), p_bname VARCHAR(50))
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE v_result INT;
    SELECT COUNT(*) INTO v_result FROM myweb_bname_table WHERE isbn = p_isbn AND bname LIKE CONCAT('%', p_bname, '%');
    RETURN v_result;
END //

-- 创建检查作者的函数
CREATE FUNCTION check_author(p_isbn VARCHAR(50), p_author VARCHAR(50))
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE v_result INT;
    SELECT COUNT(*) INTO v_result FROM myweb_bname_table WHERE isbn = p_isbn AND author LIKE CONCAT('%', p_author, '%');
    RETURN v_result;
END //

-- 创建检查出版社的函数
CREATE FUNCTION check_pub(p_isbn VARCHAR(50), p_pub VARCHAR(50))
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE v_result INT;
    SELECT COUNT(*) INTO v_result FROM myweb_bname_table WHERE isbn = p_isbn AND pub LIKE CONCAT('%', p_pub, '%');
    RETURN v_result;
END //

-- 创建检查出版年月的函数
CREATE FUNCTION check_pubtime(p_isbn VARCHAR(50), p_pubtime DATE)
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE v_result INT;
    SELECT COUNT(*) INTO v_result FROM myweb_bname_table WHERE isbn = p_isbn AND pubtime = p_pubtime;
    RETURN v_result;
END //

-- 创建管理书籍库存的存储过程
CREATE PROCEDURE manage_book_stock(
    IN p_isbn VARCHAR(50),
    IN p_num INT,
    IN p_bname VARCHAR(50),
    IN p_author VARCHAR(50),
    IN p_pub VARCHAR(50),
    IN p_pubtime DATE,
    IN p_admin_id VARCHAR(10),
    OUT p_message VARCHAR(100)
)
BEGIN
    DECLARE v_result INT;
    DECLARE v_count INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_message = '操作失败，已回滚事务';
    END;

    -- 开始事务
    START TRANSACTION;

    -- 检查书籍是否存在于 Bname_Table 中
    SELECT COUNT(*) INTO v_count FROM myweb_bname_table WHERE isbn = p_isbn;
    
    manage_book_stock0: BEGIN
    IF v_count > 0 THEN
        -- 处理旧书录入
        IF p_bname IS NOT NULL THEN
            SET v_result = check_bname(p_isbn, p_bname);
            IF v_result = 0 THEN
                SET p_message = '检测到旧书录入，且书名信息不匹配，请检查';
                LEAVE manage_book_stock0;
            END IF;
        END IF;
        
        IF p_author IS NOT NULL THEN
            SET v_result = check_author(p_isbn, p_author);
            IF v_result = 0 THEN
                SET p_message = '检测到旧书录入，且作者信息不匹配，请检查';
                LEAVE manage_book_stock0;
            END IF;
        END IF;
        
        IF p_pub IS NOT NULL THEN
            SET v_result = check_pub(p_isbn, p_pub);
            IF v_result = 0 THEN
                SET p_message = '检测到旧书录入，且出版社信息不匹配，请检查';
                LEAVE manage_book_stock0;
            END IF;
        END IF;
        
        IF p_pubtime IS NOT NULL THEN
            SET v_result = check_pubtime(p_isbn, p_pubtime);
            IF v_result = 0 THEN
                SET p_message = '检测到旧书录入，且出版年月不匹配，请检查';
                LEAVE manage_book_stock0;
            END IF;
        END IF;
        
        -- 为每本书插入到 Book_Table
        SET v_result = 0;
        WHILE v_result < p_num DO
            INSERT INTO myweb_book_table (isbn_id, status, admin_id)
            VALUES (p_isbn, '未借出', p_admin_id);
            SET v_result = v_result + 1;
        END WHILE;
        
        SET p_message = '旧书入库成功！';
    ELSE
        -- 处理新书录入
        IF p_bname IS NULL OR p_author IS NULL OR p_pub IS NULL OR p_pubtime IS NULL THEN
            SET p_message = '检测到新书录入，请完整填写信息';
            LEAVE manage_book_stock0;
        END IF;
        
        -- 插入到 Bname_Table
        INSERT INTO myweb_bname_table (isbn, bname, author, pub, pubtime, admin_id)
        VALUES (p_isbn, p_bname, p_author, p_pub, p_pubtime, p_admin_id);
        
        -- 为每本书插入到 Book_Table
        SET v_result = 0;
        WHILE v_result < p_num DO
            INSERT INTO myweb_book_table (isbn_id, status, admin_id)
            VALUES (p_isbn, '未借出', p_admin_id);
            SET v_result = v_result + 1;
        END WHILE;
        
        SET p_message = '新书入库成功！';
    END IF;
    END;

    -- 提交事务
    COMMIT;
END //

DELIMITER ;
