DELIMITER $$
DROP TRIGGER IF EXISTS after_reserve_delete$$
CREATE TRIGGER after_reserve_delete
AFTER DELETE ON myweb_reserve_table
FOR EACH ROW
BEGIN
    UPDATE myweb_book_table
    SET status = '未借出'
    WHERE bid = OLD.bid_id;
END$$

DELIMITER ;