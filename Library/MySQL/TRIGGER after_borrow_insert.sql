DELIMITER $$
DROP TRIGGER IF EXISTS after_borrow_insert$$
CREATE TRIGGER after_borrow_insert
AFTER INSERT ON myweb_borrow_table
FOR EACH ROW
BEGIN
    UPDATE myweb_book_table
    SET status = '已借出'
    WHERE bid = NEW.bid_id;
END$$

DELIMITER ;